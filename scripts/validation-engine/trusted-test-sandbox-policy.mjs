// The sandbox policy describes Linux paths even when its contract runs on Windows.
import path from 'node:path/posix';

export const HOST_PATHS_TO_HIDE = Object.freeze([
  '/etc',
  '/home',
  '/root',
  '/run',
  '/var',
  '/tmp',
  '/sys',
  '/media',
  '/mnt',
  '/opt',
  '/srv',
  '/usr/local',
  '/workspace',
  '/workspaces',
  '/data',
  '/backup',
  '/backups',
  '/volumes',
  '/secrets',
  '/credentials',
]);

function isWithin(root, candidate) {
  const relative = path.relative(root, candidate);
  return (
    relative === '' ||
    (relative !== '..' &&
      !relative.startsWith('..' + path.sep) &&
      !path.isAbsolute(relative))
  );
}

export function hostPathsToHide(sourceRoot) {
  const checkout = path.resolve(sourceRoot);
  const filesystemRoot = path.parse(checkout).root;
  if (checkout === filesystemRoot)
    throw new Error('The candidate checkout cannot be the filesystem root.');

  if (HOST_PATHS_TO_HIDE.some((directory) => isWithin(directory, checkout)))
    return [...HOST_PATHS_TO_HIDE];

  const parent = path.dirname(checkout);
  return [
    ...HOST_PATHS_TO_HIDE,
    parent === filesystemRoot ? checkout : parent,
  ];
}

export function sandboxMountOperations({
  workspace,
  runDirectory,
  externalMounts,
  dependencyMounts,
  hiddenDirectories,
  guestWorkspace,
  guestRun,
  markerFile,
  guestMarker,
}) {
  const operations = hiddenDirectories.map((directory) => ({
    type: 'tmpfs',
    path: directory,
    hostMask: true,
  }));
  operations.push(
    { type: 'dir', path: guestWorkspace },
    { type: 'dir', path: guestRun },
    { type: 'bind-fd', source: workspace, target: guestWorkspace },
    { type: 'bind-fd', source: runDirectory, target: guestRun },
  );
  for (const [source, target] of externalMounts)
    operations.push({ type: 'ro-bind-fd', source, target });
  for (const [source, target] of dependencyMounts)
    operations.push({ type: 'ro-bind-fd', source, target });
  operations.push({ type: 'ro-bind-fd', source: markerFile, target: guestMarker });
  return operations;
}

const sensitiveName =
  /^(?:[.]env(?:$|[.](?!example$)[^/]+)|[.]ssh|[.]aws|[.]gnupg|id_(?:rsa|ed25519)|[.]git-credentials|[.]npmrc|[.]pypirc|[.]netrc|[^/]+[.](?:pem|key))$/iu;
const sensitiveCredentialName =
  /^[.]?(?:auth(?:entication)?|tokens?|credentials?|secrets?|private[-_]?keys?|api[-_]?keys?|access[-_]?tokens?|refresh[-_]?tokens?|client[-_]?secrets?)$/iu;
const sensitiveCredentialConfigFile =
  /^[.]?(?:auth(?:entication)?|tokens?|credentials?|secrets?|private[-_]?keys?|api[-_]?keys?|access[-_]?tokens?|refresh[-_]?tokens?|client[-_]?secrets?)[.](?:json|ya?ml|toml|ini|cfg|conf|env(?:[.](?!example$)[^/]+)?|properties|xml|txt)$/iu;
const qualifiedCredentialSourceName =
  /^(?:[^._-]+[._-])?(?:tokens?|credentials?|secrets?)(?:[._-](?!(?:manager|parser|service|client|store|provider|package|module|checker|scanning|persistence|differential|filter|policy|schema|template|example|sample|source)(?:$|[._-]))[^/]+)*$/iu;
const qualifiedAuthSourceName = /^[^._-]+[._-]auth(?:entication)?$/iu;
const credentialEnvironmentExampleFile =
  /^[.]?(?:auth(?:entication)?|tokens?|credentials?|secrets?)[.]env[.]example$/iu;
const qualifiedAuthConfigFile =
  /^[^/]+[._-]auth(?:entication)?[.](?:json|ya?ml|toml|ini|cfg|conf|env|properties|xml|txt)$/iu;
const qualifiedCredentialConfigFile =
  /^(?:[^/]+[._-])?(?:tokens?|credentials?|secrets?)(?:[._-](?!(?:manager|parser|service|client|store|provider|package|module|checker|scanning|persistence|differential|filter|policy|schema|template|example|sample|source)(?:$|[._-]))[^/.]+)*[.](?:json|ya?ml|toml|ini|cfg|conf|env(?:[.](?!example$)[^/]+)?|properties|xml|txt)$/iu;
const sensitiveCredentialMaterialFile =
  /(?:^|[._-])(?:private[._-]?keys?|api[._-]?keys?|access[._-]?tokens?|refresh[._-]?tokens?|client[._-]?secrets?)(?=$|[._-])/iu;
const camelCaseCredentialMaterialFile =
  /(?:(?<=[a-z0-9])(?:PrivateKeys?|privateKeys?|ApiKeys?|APIKeys?|ApiTokens?|APITokens?|AccessTokens?|RefreshTokens?|ClientTokens?|ClientCredentials?|ClientSecrets?|ServiceAccountTokens?|ServiceAccountCredentials?|ServiceAccountSecrets?)|^(?:prod(?:uction)?|dev(?:elopment)?|test(?:ing)?|stage|staging|local|qa|live|github|gitlab|bitbucket|aws|azure|gcp|google|slack|discord|oauth|jwt|bearer)(?:Auth(?:entication)?|Tokens?|Credentials?|Secrets?)(?=$|[._-]))/iu;
const qualifiedCredentialDirectoryName =
  /^(?:[^/]+[._-](?:auth(?:entication)?|tokens?|credentials?|secrets?|private[._-]?keys?|api[._-]?keys?|access[._-]?tokens?|refresh[._-]?tokens?|client[._-]?secrets?)|(?:tokens?|credentials?|secrets?|private[._-]?keys?|api[._-]?keys?|access[._-]?tokens?|refresh[._-]?tokens?|client[._-]?secrets?)[._-](?!(?:manager|parser|service|client|store|provider|package|module|checker|scanning|persistence|differential|filter|policy|schema|template|example|sample|source)(?:$|[._-]))[^/]+)$/iu;
const sourceTreeDirectory =
  /^(?:src|source|packages|apps|web|dashboard|client-go|client-python|client-ts|crates|scripts|lib|tests?|__tests__|fixtures?)$/iu;
const knownApiKeysPage = 'dashboard/src/pages/ApiKeys.tsx';
const knownCredentialNameExceptions = new Set([
  'src/auth.ts',
  'src/authentication.ts',
  'web/src/lib/token.js',
  'vendor/mainline/src/rpc/server/tokens.rs',
  'crates/slskr/src/private_gateway_owners/peer_authentication.rs',
  'dashboard/src/pages/ApiKeys.tsx',
  'docs/credential-storage.md',
]);

export function isSensitiveCandidatePath(relativePath) {
  const normalizedPath = relativePath.replaceAll(String.fromCharCode(92), '/');
  const segments = normalizedPath.split('/');
  if (segments.includes('.git') || segments.includes('node_modules'))
    return true;
  if (segments.some((segment) => sensitiveName.test(segment)))
    return true;

  const filename = segments.at(-1) ?? '';
  const directories = segments.slice(0, -1);
  const extensionSeparator = filename.lastIndexOf('.');
  const sourceName = extensionSeparator > 0
    ? filename.slice(0, extensionSeparator)
    : filename;
  const sensitiveCredentialSourceFile =
    sensitiveCredentialName.test(sourceName) ||
    qualifiedCredentialSourceName.test(sourceName) ||
    qualifiedAuthSourceName.test(sourceName);
  if (
    sensitiveCredentialName.test(filename) ||
    sensitiveCredentialConfigFile.test(filename) ||
    qualifiedAuthConfigFile.test(filename) ||
    qualifiedCredentialConfigFile.test(filename) ||
    (!credentialEnvironmentExampleFile.test(filename) &&
      sensitiveCredentialSourceFile &&
      !knownCredentialNameExceptions.has(normalizedPath))
  )
    return true;
  if (
    (sensitiveCredentialMaterialFile.test(filename) ||
      camelCaseCredentialMaterialFile.test(filename)) &&
    normalizedPath !== knownApiKeysPage
  ) return true;

  const credentialDirectoryIndex = directories.findIndex((segment) =>
    sensitiveCredentialName.test(segment) ||
    qualifiedCredentialDirectoryName.test(segment),
  );
  if (credentialDirectoryIndex < 0) return false;

  const sourceTreeBeforeCredentialDirectory = directories
    .slice(0, credentialDirectoryIndex)
    .some((segment) => sourceTreeDirectory.test(segment));
  return !sourceTreeBeforeCredentialDirectory;
}
