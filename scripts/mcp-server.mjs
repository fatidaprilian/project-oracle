#!/usr/bin/env node

import { existsSync, readFileSync } from 'node:fs';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { spawn } from 'node:child_process';
import { dirname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

const SCRIPT_FILE_PATH = fileURLToPath(import.meta.url);
const REPOSITORY_ROOT = resolve(dirname(SCRIPT_FILE_PATH), '..');
const STATE_DIRECTORY = resolve(REPOSITORY_ROOT, '.agent-context', 'state');
const DEFAULT_PROTOCOL_VERSION = '2024-11-05';
const DEFAULT_FETCH_TIMEOUT_MS = 15000;
const DEFAULT_FETCH_MAX_CHARS = 6000;
const MAX_FETCH_MAX_CHARS = 20000;
const DEFAULT_TREND_WINDOW_DAYS = 90;
const MAX_TREND_PACKAGES = 10;
const FALLBACK_PACKAGE_VERSION = '0.0.0-local';

function resolvePackageVersion() {
  try {
    const parsedPackageManifest = JSON.parse(
      readFileSync(resolve(REPOSITORY_ROOT, 'package.json'), 'utf8')
    );
    const rawVersion = typeof parsedPackageManifest?.version === 'string'
      ? parsedPackageManifest.version.trim()
      : '';

    return rawVersion || FALLBACK_PACKAGE_VERSION;
  } catch {
    return FALLBACK_PACKAGE_VERSION;
  }
}

const PACKAGE_VERSION = resolvePackageVersion();

const TEST_SUITE_ARGS = {
  full: ['--test', './tests/cli-smoke.test.mjs', './tests/mcp-server.test.mjs', './tests/llm-judge.test.mjs', './tests/enterprise-ops.test.mjs'],
  cli: ['--test', './tests/cli-smoke.test.mjs'],
  enterprise: ['--test', './tests/enterprise-ops.test.mjs'],
  'llm-judge': ['--test', './tests/llm-judge.test.mjs'],
};

const INTERNAL_SCRIPT_PATHS = {
  validate: resolve(REPOSITORY_ROOT, 'scripts', 'validate.mjs'),
  release_gate: resolve(REPOSITORY_ROOT, 'scripts', 'release-gate.mjs'),
  forbidden_content_check: resolve(REPOSITORY_ROOT, 'scripts', 'forbidden-content-check.mjs'),
};

function getAvailableTestSuites() {
  return Object.entries(TEST_SUITE_ARGS)
    .filter(([, commandArguments]) => (
      Array.isArray(commandArguments)
      && commandArguments.length > 1
      && commandArguments
        .slice(1)
        .every((relativeTestPath) => existsSync(resolve(REPOSITORY_ROOT, relativeTestPath)))
    ))
    .map(([suiteName]) => suiteName);
}

const AVAILABLE_TEST_SUITES = getAvailableTestSuites();

function buildToolDefinitions() {
  const toolDefinitions = [];

  if (existsSync(INTERNAL_SCRIPT_PATHS.validate)) {
    toolDefinitions.push({
      name: 'validate',
      description: 'Run repository validation checks.',
      inputSchema: {
        type: 'object',
        properties: {},
        additionalProperties: false,
      },
    });
  }

  if (AVAILABLE_TEST_SUITES.length > 0) {
    toolDefinitions.push({
      name: 'test',
      description: 'Run test suites (full or targeted).',
      inputSchema: {
        type: 'object',
        properties: {
          suite: {
            type: 'string',
            enum: AVAILABLE_TEST_SUITES,
            description: 'Target test suite. Defaults to the first available suite.',
          },
        },
        additionalProperties: false,
      },
    });
  }

  if (existsSync(INTERNAL_SCRIPT_PATHS.release_gate)) {
    toolDefinitions.push({
      name: 'release_gate',
      description: 'Run release gate checks.',
      inputSchema: {
        type: 'object',
        properties: {},
        additionalProperties: false,
      },
    });
  }

  if (existsSync(INTERNAL_SCRIPT_PATHS.forbidden_content_check)) {
    toolDefinitions.push({
      name: 'forbidden_content_check',
      description: 'Run forbidden content scan used by publish gate.',
      inputSchema: {
        type: 'object',
        properties: {},
        additionalProperties: false,
      },
    });
  }

  toolDefinitions.push(
    {
      name: 'research_fetch',
      description: 'Fetch external documentation/news content and return query-focused excerpts with citation metadata.',
      inputSchema: {
        type: 'object',
        properties: {
          url: {
            type: 'string',
            description: 'Absolute HTTP/HTTPS URL to fetch.',
          },
          query: {
            type: 'string',
            description: 'Optional search query used to extract focused excerpts.',
          },
          maxChars: {
            type: 'integer',
            description: 'Maximum characters to return when query is not provided (default 6000, max 20000).',
          },
        },
        required: ['url'],
        additionalProperties: false,
      },
    },
    {
      name: 'trend_snapshot',
      description: 'Generate ecosystem trend snapshot from npm registry metadata with source timestamps.',
      inputSchema: {
        type: 'object',
        properties: {
          packages: {
            type: 'array',
            items: { type: 'string' },
            description: 'Package names to inspect (max 10).',
          },
          windowDays: {
            type: 'integer',
            description: 'Release activity window in days (default 90).',
          },
        },
        required: ['packages'],
        additionalProperties: false,
      },
    },
    {
      name: 'state_read',
      description: 'Read a file from .agent-context/state for cross-session continuity.',
      inputSchema: {
        type: 'object',
        properties: {
          path: {
            type: 'string',
            description: 'Path relative to .agent-context/state (for example memory-continuity-benchmark.json).',
          },
        },
        required: ['path'],
        additionalProperties: false,
      },
    },
    {
      name: 'state_write',
      description: 'Write a file under .agent-context/state for cross-session continuity updates.',
      inputSchema: {
        type: 'object',
        properties: {
          path: {
            type: 'string',
            description: 'Path relative to .agent-context/state.',
          },
          content: {
            type: 'string',
            description: 'UTF-8 content to write.',
          },
          mode: {
            type: 'string',
            enum: ['overwrite', 'append'],
            description: 'Write mode. Defaults to overwrite.',
          },
        },
        required: ['path', 'content'],
        additionalProperties: false,
      },
    },
  );

  return toolDefinitions;
}

const TOOL_DEFINITIONS = buildToolDefinitions();

let incomingBuffer = Buffer.alloc(0);

function writeMessage(payload) {
  const serializedPayload = JSON.stringify(payload);
  // MCP standard: line-delimited JSON (no Content-Length header)
  process.stdout.write(serializedPayload + '\n');
}

function sendResponse(id, result) {
  writeMessage({
    jsonrpc: '2.0',
    id,
    result,
  });
}

function sendError(id, code, message, data) {
  writeMessage({
    jsonrpc: '2.0',
    id,
    error: {
      code,
      message,
      data,
    },
  });
}

function normalizeToolName(rawToolName) {
  return typeof rawToolName === 'string' ? rawToolName.trim() : '';
}

function buildCommandOutput(commandLabel, commandArguments, exitCode, stdoutContent, stderrContent) {
  const outputSections = [
    `Command: node ${commandArguments.join(' ')}`,
    `Exit code: ${exitCode}`,
  ];

  if (stdoutContent.trim().length > 0) {
    outputSections.push(`STDOUT:\n${stdoutContent.trimEnd()}`);
  }

  if (stderrContent.trim().length > 0) {
    outputSections.push(`STDERR:\n${stderrContent.trimEnd()}`);
  }

  return [
    `[${commandLabel}]`,
    outputSections.join('\n\n'),
  ].join('\n\n');
}

function buildJsonResult(payload, isError = false) {
  return {
    content: [
      {
        type: 'text',
        text: JSON.stringify(payload, null, 2),
      },
    ],
    isError,
  };
}

function normalizePlainText(rawText) {
  return rawText
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&nbsp;/gi, ' ')
    .replace(/&amp;/gi, '&')
    .replace(/&lt;/gi, '<')
    .replace(/&gt;/gi, '>')
    .replace(/\s+/g, ' ')
    .trim();
}

function extractQuerySnippets(textContent, queryText) {
  const normalizedQuery = String(queryText || '').trim().toLowerCase();
  if (!normalizedQuery) {
    return [];
  }

  const normalizedContent = String(textContent || '');
  const normalizedLowerContent = normalizedContent.toLowerCase();
  const snippets = [];
  let searchStartIndex = 0;

  while (snippets.length < 5) {
    const matchedIndex = normalizedLowerContent.indexOf(normalizedQuery, searchStartIndex);
    if (matchedIndex === -1) {
      break;
    }

    const contextRadius = 180;
    const snippetStart = Math.max(0, matchedIndex - contextRadius);
    const snippetEnd = Math.min(normalizedContent.length, matchedIndex + normalizedQuery.length + contextRadius);
    const prefix = snippetStart > 0 ? '...' : '';
    const suffix = snippetEnd < normalizedContent.length ? '...' : '';
    snippets.push(`${prefix}${normalizedContent.slice(snippetStart, snippetEnd).trim()}${suffix}`);
    searchStartIndex = matchedIndex + normalizedQuery.length;
  }

  return snippets;
}

async function fetchWithTimeout(targetUrl, timeoutMs) {
  const fetchController = new AbortController();
  const timeoutHandle = setTimeout(() => fetchController.abort(), timeoutMs);

  try {
    return await fetch(targetUrl, {
      signal: fetchController.signal,
      headers: {
        'User-Agent': `agentic-senior-core/${PACKAGE_VERSION}`,
      },
    });
  } finally {
    clearTimeout(timeoutHandle);
  }
}

async function runResearchFetchTool(toolArguments = {}) {
  const targetUrl = String(toolArguments.url || '').trim();
  const queryText = typeof toolArguments.query === 'string' ? toolArguments.query.trim() : '';
  const maxCharsInput = Number(toolArguments.maxChars);
  const maxChars = Number.isFinite(maxCharsInput)
    ? Math.max(200, Math.min(MAX_FETCH_MAX_CHARS, Math.floor(maxCharsInput)))
    : DEFAULT_FETCH_MAX_CHARS;

  if (!/^https?:\/\//i.test(targetUrl)) {
    return buildJsonResult({
      error: 'Invalid url. Provide absolute HTTP/HTTPS URL.',
      input: targetUrl,
    }, true);
  }

  try {
    const startedAt = new Date().toISOString();
    const fetchResponse = await fetchWithTimeout(targetUrl, DEFAULT_FETCH_TIMEOUT_MS);
    const rawBody = await fetchResponse.text();
    const plainTextBody = normalizePlainText(rawBody);
    const querySnippets = queryText ? extractQuerySnippets(plainTextBody, queryText) : [];
    const selectedContent = querySnippets.length > 0
      ? querySnippets.join('\n\n')
      : plainTextBody.slice(0, maxChars);

    return buildJsonResult({
      source: {
        url: targetUrl,
        status: fetchResponse.status,
        ok: fetchResponse.ok,
        fetchedAt: new Date().toISOString(),
        requestedAt: startedAt,
        contentType: fetchResponse.headers.get('content-type') || null,
      },
      query: queryText || null,
      excerptCount: querySnippets.length,
      truncated: !queryText && plainTextBody.length > selectedContent.length,
      content: selectedContent,
    }, !fetchResponse.ok);
  } catch (error) {
    return buildJsonResult({
      error: error instanceof Error ? error.message : String(error),
      source: targetUrl,
    }, true);
  }
}

async function runTrendSnapshotTool(toolArguments = {}) {
  const packageInputs = Array.isArray(toolArguments.packages)
    ? toolArguments.packages.filter((packageName) => typeof packageName === 'string' && packageName.trim().length > 0)
    : [];
  const packageNames = Array.from(new Set(packageInputs.map((packageName) => packageName.trim()))).slice(0, MAX_TREND_PACKAGES);
  const windowDaysInput = Number(toolArguments.windowDays);
  const windowDays = Number.isFinite(windowDaysInput)
    ? Math.max(1, Math.min(3650, Math.floor(windowDaysInput)))
    : DEFAULT_TREND_WINDOW_DAYS;

  if (packageNames.length === 0) {
    return buildJsonResult({
      error: 'packages[] must include at least one package name.',
    }, true);
  }

  const nowTimestamp = Date.now();
  const windowStartTimestamp = nowTimestamp - (windowDays * 24 * 60 * 60 * 1000);
  const packageReports = [];

  for (const packageName of packageNames) {
    const registryUrl = `https://registry.npmjs.org/${encodeURIComponent(packageName)}`;

    try {
      const response = await fetchWithTimeout(registryUrl, DEFAULT_FETCH_TIMEOUT_MS);
      if (!response.ok) {
        packageReports.push({
          package: packageName,
          source: registryUrl,
          status: response.status,
          error: `Registry request failed with HTTP ${response.status}`,
        });
        continue;
      }

      const registryPayload = await response.json();
      const latestVersion = registryPayload?.['dist-tags']?.latest || null;
      const releaseTimes = Object.entries(registryPayload?.time || {})
        .filter(([versionName, publishedAt]) => {
          if (versionName === 'created' || versionName === 'modified') {
            return false;
          }

          return typeof publishedAt === 'string' && Number.isFinite(Date.parse(publishedAt));
        })
        .map(([versionName, publishedAt]) => ({
          version: versionName,
          publishedAt,
          publishedAtMs: Date.parse(publishedAt),
        }))
        .sort((leftEntry, rightEntry) => rightEntry.publishedAtMs - leftEntry.publishedAtMs);

      const releasesInWindow = releaseTimes.filter((releaseEntry) => releaseEntry.publishedAtMs >= windowStartTimestamp);
      const latestPublishedAt = latestVersion && typeof registryPayload?.time?.[latestVersion] === 'string'
        ? registryPayload.time[latestVersion]
        : registryPayload?.time?.modified || null;

      packageReports.push({
        package: packageName,
        source: registryUrl,
        latestVersion,
        latestPublishedAt,
        releasesInWindow: releasesInWindow.length,
        recentReleases: releasesInWindow.slice(0, 5).map((releaseEntry) => ({
          version: releaseEntry.version,
          publishedAt: releaseEntry.publishedAt,
        })),
      });
    } catch (error) {
      packageReports.push({
        package: packageName,
        source: registryUrl,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  const errorCount = packageReports.filter((packageReport) => typeof packageReport.error === 'string').length;

  return buildJsonResult({
    generatedAt: new Date().toISOString(),
    windowDays,
    packageCount: packageNames.length,
    errorCount,
    packages: packageReports,
    citation: {
      source: 'npm registry public API',
      fetchedAt: new Date().toISOString(),
    },
  }, errorCount > 0);
}

function resolveStatePath(relativeStatePath) {
  const normalizedRelativePath = String(relativeStatePath || '').replace(/\\/g, '/').replace(/^\/+/, '').trim();
  if (!normalizedRelativePath) {
    throw new Error('path is required and must be relative to .agent-context/state');
  }

  const resolvedStatePath = resolve(STATE_DIRECTORY, normalizedRelativePath);
  const stateRootPrefix = `${STATE_DIRECTORY}${sep}`;
  if (resolvedStatePath !== STATE_DIRECTORY && !resolvedStatePath.startsWith(stateRootPrefix)) {
    throw new Error('path traversal is not allowed outside .agent-context/state');
  }

  return {
    normalizedRelativePath,
    resolvedStatePath,
  };
}

async function runStateReadTool(toolArguments = {}) {
  try {
    const { normalizedRelativePath, resolvedStatePath } = resolveStatePath(toolArguments.path);
    const fileContent = await readFile(resolvedStatePath, 'utf8');

    return buildJsonResult({
      path: normalizedRelativePath,
      readAt: new Date().toISOString(),
      bytes: Buffer.byteLength(fileContent, 'utf8'),
      content: fileContent,
    });
  } catch (error) {
    return buildJsonResult({
      error: error instanceof Error ? error.message : String(error),
      path: toolArguments.path || null,
    }, true);
  }
}

async function runStateWriteTool(toolArguments = {}) {
  const writeMode = toolArguments.mode === 'append' ? 'append' : 'overwrite';
  const contentToWrite = typeof toolArguments.content === 'string' ? toolArguments.content : '';

  if (typeof toolArguments.content !== 'string') {
    return buildJsonResult({
      error: 'content must be a string.',
    }, true);
  }

  try {
    const { normalizedRelativePath, resolvedStatePath } = resolveStatePath(toolArguments.path);
    await mkdir(dirname(resolvedStatePath), { recursive: true });

    if (writeMode === 'append') {
      await writeFile(resolvedStatePath, contentToWrite, { encoding: 'utf8', flag: 'a' });
    } else {
      await writeFile(resolvedStatePath, contentToWrite, 'utf8');
    }

    return buildJsonResult({
      path: normalizedRelativePath,
      wroteAt: new Date().toISOString(),
      mode: writeMode,
      bytesWritten: Buffer.byteLength(contentToWrite, 'utf8'),
    });
  } catch (error) {
    return buildJsonResult({
      error: error instanceof Error ? error.message : String(error),
      path: toolArguments.path || null,
      mode: writeMode,
    }, true);
  }
}

function runNodeCommand(commandLabel, commandArguments) {
  return new Promise((resolveResult) => {
    const childProcess = spawn(process.execPath, commandArguments, {
      cwd: REPOSITORY_ROOT,
      env: process.env,
    });

    let stdoutContent = '';
    let stderrContent = '';

    childProcess.stdout.on('data', (chunk) => {
      stdoutContent += chunk.toString('utf8');
    });

    childProcess.stderr.on('data', (chunk) => {
      stderrContent += chunk.toString('utf8');
    });

    childProcess.on('error', (error) => {
      resolveResult({
        content: [
          {
            type: 'text',
            text: `[${commandLabel}] Failed to start command: ${error.message}`,
          },
        ],
        isError: true,
      });
    });

    childProcess.on('close', (exitCode) => {
      const normalizedExitCode = typeof exitCode === 'number' ? exitCode : 1;
      resolveResult({
        content: [
          {
            type: 'text',
            text: buildCommandOutput(
              commandLabel,
              commandArguments,
              normalizedExitCode,
              stdoutContent,
              stderrContent
            ),
          },
        ],
        isError: normalizedExitCode !== 0,
      });
    });
  });
}

async function executeToolCall(toolName, toolArguments = {}) {
  if (toolName === 'validate') {
    if (!existsSync(INTERNAL_SCRIPT_PATHS.validate)) {
      return buildJsonResult({
        error: 'validate tool is unavailable because scripts/validate.mjs is missing in this workspace.',
      }, true);
    }

    return runNodeCommand('validate', ['./scripts/validate.mjs']);
  }

  if (toolName === 'test') {
    if (AVAILABLE_TEST_SUITES.length === 0) {
      return buildJsonResult({
        error: 'test tool is unavailable because the managed test suites are not present in this workspace.',
      }, true);
    }

    const defaultSuite = AVAILABLE_TEST_SUITES[0];
    const requestedSuite = typeof toolArguments.suite === 'string'
      ? toolArguments.suite
      : defaultSuite;

    const selectedSuite = AVAILABLE_TEST_SUITES.includes(requestedSuite)
      ? requestedSuite
      : defaultSuite;
    return runNodeCommand(`test:${selectedSuite}`, TEST_SUITE_ARGS[selectedSuite]);
  }

  if (toolName === 'release_gate') {
    if (!existsSync(INTERNAL_SCRIPT_PATHS.release_gate)) {
      return buildJsonResult({
        error: 'release_gate tool is unavailable because scripts/release-gate.mjs is missing in this workspace.',
      }, true);
    }

    return runNodeCommand('release_gate', ['./scripts/release-gate.mjs']);
  }

  if (toolName === 'forbidden_content_check') {
    if (!existsSync(INTERNAL_SCRIPT_PATHS.forbidden_content_check)) {
      return buildJsonResult({
        error: 'forbidden_content_check tool is unavailable because scripts/forbidden-content-check.mjs is missing in this workspace.',
      }, true);
    }

    return runNodeCommand('forbidden_content_check', ['./scripts/forbidden-content-check.mjs']);
  }

  if (toolName === 'research_fetch') {
    return runResearchFetchTool(toolArguments);
  }

  if (toolName === 'trend_snapshot') {
    return runTrendSnapshotTool(toolArguments);
  }

  if (toolName === 'state_read') {
    return runStateReadTool(toolArguments);
  }

  if (toolName === 'state_write') {
    return runStateWriteTool(toolArguments);
  }

  return {
    content: [
      {
        type: 'text',
        text: `Unknown tool: ${toolName}`,
      },
    ],
    isError: true,
  };
}

async function handleRequest(requestMessage) {
  const requestId = requestMessage.id;
  const requestMethod = requestMessage.method;
  const requestParams = requestMessage.params || {};

  if (typeof requestMethod !== 'string') {
    if (typeof requestId !== 'undefined') {
      sendError(requestId, -32600, 'Invalid Request');
    }
    return;
  }

  if (requestMethod === 'initialize') {
    const negotiatedProtocolVersion = typeof requestParams.protocolVersion === 'string'
      ? requestParams.protocolVersion
      : DEFAULT_PROTOCOL_VERSION;

    sendResponse(requestId, {
      protocolVersion: negotiatedProtocolVersion,
      capabilities: {
        tools: {
          listChanged: false,
        },
      },
      serverInfo: {
        name: 'agentic-senior-core',
        version: PACKAGE_VERSION,
      },
    });
    return;
  }

  if (requestMethod === 'notifications/initialized') {
    return;
  }

  if (requestMethod === 'ping') {
    if (typeof requestId !== 'undefined') {
      sendResponse(requestId, {});
    }
    return;
  }

  if (requestMethod === 'tools/list') {
    sendResponse(requestId, {
      tools: TOOL_DEFINITIONS,
    });
    return;
  }

  if (requestMethod === 'tools/call') {
    const requestedToolName = normalizeToolName(requestParams.name);

    if (!requestedToolName) {
      sendError(requestId, -32602, 'Invalid params: tool name is required');
      return;
    }

    const toolResult = await executeToolCall(requestedToolName, requestParams.arguments || {});
    sendResponse(requestId, toolResult);
    return;
  }

  if (typeof requestId !== 'undefined') {
    sendError(requestId, -32601, `Method not found: ${requestMethod}`);
  }
}

function processIncomingBuffer() {
  const fullContent = incomingBuffer.toString('utf8');
  
  // Try to parse as line-delimited JSON first (modern MCP standard)
  let parseMode = 'line-delimited';
  
  // Check if Content-Length header is present (LSP-style for backward compatibility)
  if (fullContent.includes('Content-Length:')) {
    parseMode = 'content-length';
  }
  
  if (parseMode === 'content-length') {
    // LSP-style: Parse Content-Length headers
    const headerTerminatorIndex = Math.max(
      fullContent.indexOf('\r\n\r\n'),
      fullContent.indexOf('\n\n')
    );
    
    if (headerTerminatorIndex === -1) {
      return; // Incomplete header, wait for more data
    }
    
    const headerText = fullContent.slice(0, headerTerminatorIndex);
    const contentLengthMatch = headerText.match(/Content-Length:\s*(\d+)/i);
    
    if (!contentLengthMatch) {
      incomingBuffer = Buffer.alloc(0);
      return;
    }
    
    const contentLength = parseInt(contentLengthMatch[1], 10);
    const headerEndLength = fullContent[headerTerminatorIndex] === '\r' ? 4 : 2;
    const bodyStartIndex = headerTerminatorIndex + headerEndLength;
    const bodyEndIndex = bodyStartIndex + contentLength;
    
    if (fullContent.length < bodyEndIndex) {
      return; // Body not yet complete
    }
    
    const messageBody = fullContent.slice(bodyStartIndex, bodyEndIndex);
    incomingBuffer = Buffer.from(fullContent.slice(bodyEndIndex), 'utf8');
    
    try {
      const parsedRequest = JSON.parse(messageBody);
      Promise.resolve(handleRequest(parsedRequest)).catch((error) => {
        if (typeof parsedRequest?.id !== 'undefined') {
          sendError(parsedRequest.id, -32603, 'Internal error', String(error?.message || error));
        }
      });
    } catch {
      // Ignore parse errors
    }
    
    // Recursively process if there's more data
    if (incomingBuffer.length > 0) {
      processIncomingBuffer();
    }
  } else {
    // Line-delimited: parse one JSON per line
    const lines = fullContent.split('\n');
    
    // Keep incomplete last line in buffer
    if (fullContent.endsWith('\n')) {
      incomingBuffer = Buffer.alloc(0);
    } else {
      const lastLine = lines.pop() || '';
      incomingBuffer = Buffer.from(lastLine, 'utf8');
    }
    
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      
      let parsedRequest;
      try {
        parsedRequest = JSON.parse(trimmed);
      } catch {
        // Ignore non-JSON lines
        continue;
      }
      
      Promise.resolve(handleRequest(parsedRequest)).catch((error) => {
        if (typeof parsedRequest?.id !== 'undefined') {
          sendError(parsedRequest.id, -32603, 'Internal error', String(error?.message || error));
        }
      });
    }
  }
}

process.stdin.on('data', (chunk) => {
  incomingBuffer = Buffer.concat([incomingBuffer, chunk]);
  processIncomingBuffer();
});

process.stdin.on('end', () => {
  process.exit(0);
});

process.on('SIGINT', () => {
  process.exit(0);
});
