import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import { deleteDirectory, deleteFile, list } from '../../../lib/files';
import { toDisplayError } from '../../../lib/errors';
import { formatBytes, formatDate } from '../../../lib/util';
import { LoaderSegment } from '../../Shared';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import { toast } from 'react-toastify';
import { Header, Icon, Message, Modal, Table } from 'semantic-ui-react';

const fileStoragePath = (subdirectory, fullName) =>
  [...subdirectory, fullName].filter(Boolean).join('/');

const isRecord = (value) =>
  value && typeof value === 'object' && !Array.isArray(value);

const asRecords = (value) =>
  (Array.isArray(value) ? value : []).filter(isRecord);

const normalizeListing = (value) => ({
  directories: asRecords(value?.directories).filter(
    (entry) => typeof entry.name === 'string' && entry.name,
  ),
  files: asRecords(value?.files).filter(
    (entry) => typeof entry.name === 'string' && entry.name,
  ),
});

const reportFileOperationError = (error) => {
  console.error('[Files] Remote file operation failed:', error);
  toast.error(toDisplayError(error, 'File operation failed'));
};

const FileRow = ({
  fullName,
  length,
  modifiedAt,
  name,
  onDelete,
  deleting = false,
  remoteFileManagement,
  root,
  subdirectory,
}) => (
  <Table.Row key={fullName}>
    <Table.Cell>
      <Icon name="file outline" />
      {name}
    </Table.Cell>
    <Table.Cell>{modifiedAt ? formatDate(modifiedAt) : ''}</Table.Cell>
    <Table.Cell>{length ? formatBytes(length) : ''}</Table.Cell>
    <Table.Cell>
      {remoteFileManagement ? (
        <Modal
          actions={[
            'Cancel',
            {
              content: interfaceText("Delete"),
              key: 'done',
              negative: true,
              onClick: onDelete,
            },
          ]}
          centered
          content={interfaceText("Are you sure you want to delete file '{fullName}'?", { "fullName": (fullName) })}
          header={
            <Header
              content={interfaceText("Confirm File Delete")}
              icon="trash alternate"
             {...interfaceTextProps("Confirm File Delete")}/>
          }
          size="small"
          trigger={
            <Icon
              color="red"
              disabled={deleting}
              loading={deleting}
              name="trash alternate"
              style={{ cursor: deleting ? 'wait' : 'pointer' }}
            />
          }
         {...interfaceTextProps("Are you sure you want to delete file '{fullName}'?")}/>
      ) : null}
    </Table.Cell>
  </Table.Row>
);

const DirectoryRow = ({
  deletable = true,
  fullName,
  modifiedAt,
  name,
  onClick = () => {},
  onDelete,
  deleting = false,
  remoteFileManagement,
  root,
  subdirectory,
}) => (
  <Table.Row key={name}>
    <Table.Cell
      onClick={onClick}
      style={{ cursor: 'pointer' }}
    >
      <Icon name="folder" />
      {name}
    </Table.Cell>
    <Table.Cell>{modifiedAt ? formatDate(modifiedAt) : ''}</Table.Cell>
    <Table.Cell />
    <Table.Cell>
      {remoteFileManagement && deletable ? (
        <Modal
          actions={[
            'Cancel',
            {
              content: interfaceText("Delete"),
              key: 'done',
              negative: true,
              onClick: onDelete,
            },
          ]}
          centered
          content={interfaceText("Are you sure you want to delete directory '{fullName}'?", { "fullName": (fullName) })}
          header={
            <Header
              content={interfaceText("Confirm Directory Delete")}
              icon="trash alternate"
             {...interfaceTextProps("Confirm Directory Delete")}/>
          }
          size="small"
          trigger={
            <Icon
              color="red"
              disabled={deleting}
              loading={deleting}
              name="trash alternate"
              style={{ cursor: deleting ? 'wait' : 'pointer' }}
            />
          }
         {...interfaceTextProps("Are you sure you want to delete directory '{fullName}'?")}/>
      ) : (
        ''
      )}
    </Table.Cell>
  </Table.Row>
);

const Explorer = ({ active = true, remoteFileManagement, root }) => {
  useInterfaceLanguage();
  const [directory, setDirectory] = useState({ directories: [], files: [] });
  const [directoryError, setDirectoryError] = useState(null);
  const [subdirectory, setSubdirectory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [deletingPath, setDeletingPath] = useState('');
  const mountedRef = useRef(false);
  const requestIdRef = useRef(0);
  const deletingPathRef = useRef('');

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      requestIdRef.current += 1;
    };
  }, []);

  const refresh = useCallback(async () => {
    const requestId = ++requestIdRef.current;
    if (!active) {
      return;
    }

    setLoading(true);
    try {
      const directoryResult = await list({
        root,
        subdirectory: subdirectory.join('/'),
      });
      if (
        mountedRef.current &&
        requestId === requestIdRef.current
      ) {
        setDirectoryError(null);
        setDirectory(normalizeListing(directoryResult));
      }
    } catch (error) {
      if (
        mountedRef.current &&
        requestId === requestIdRef.current
      ) {
        setDirectoryError(toDisplayError(error, 'File listing unavailable'));
        reportFileOperationError(error);
      }
    } finally {
      if (
        mountedRef.current &&
        requestId === requestIdRef.current
      ) {
        setLoading(false);
      }
    }
  }, [active, root, subdirectory]);

  const handleDelete = useCallback(
    async ({ kind, path }) => {
      const operationKey = kind + ':' + path;
      if (
        !mountedRef.current ||
        deletingPathRef.current
      ) {
        return;
      }
      deletingPathRef.current = operationKey;
      setDeletingPath(operationKey);
      try {
        if (kind === 'file') {
          await deleteFile({ path, root });
        } else {
          await deleteDirectory({ path, root });
        }
        await refresh();
      } catch (error) {
        if (mountedRef.current) reportFileOperationError(error);
      } finally {
        deletingPathRef.current = '';
        if (mountedRef.current) setDeletingPath('');
      }
    },
    [refresh, root],
  );

  useEffect(() => {
    if (!active) {
      requestIdRef.current += 1;
      setLoading(false);
      return;
    }

    void refresh();
  }, [active, refresh]);

  useEffect(() => {
    setSubdirectory([]);
  }, [root]);

  const select = ({ path }) => {
    if (typeof path !== 'string' || !path || path === '.' || path === '..') {
      return;
    }
    setSubdirectory((previous) => [...previous, path]);
  };

  const upOneSubdirectory = () => {
    setSubdirectory((previous) => previous.slice(0, -1));
  };

  if (!active) {
    return (
      <Header
        className="explorer-working-directory"
        size="small"
      >
        <Icon name="folder" />
        {'/' + root + '/'}
      </Header>
    );
  }

  if (loading) {
    return <LoaderSegment />;
  }

  const directories = Array.isArray(directory?.directories)
    ? directory.directories
    : [];
  const files = Array.isArray(directory?.files) ? directory.files : [];
  const total = directories.length + files.length;

  return (
    <>
      <Header
        className="explorer-working-directory"
        size="small"
      >
        <Icon name="folder open" />
        {'/' + root + '/' + subdirectory.join('/')}
      </Header>
      {directoryError ? (
        <Message
          data-testid="files-load-error"
          error
        >
          <Message.Header><LocalizedText source={"Files unavailable"} /></Message.Header>
          <p>{directoryError}</p>
        </Message>
      ) : (
        <Table
          className="unstackable"
          size="large"
        >
        <Table.Header>
          <Table.Row>
            <Table.HeaderCell className="explorer-list-name">
              <LocalizedText source={"Name"} /></Table.HeaderCell>
            <Table.HeaderCell className="explorer-list-date">
              <LocalizedText source={"Date Modified"} /></Table.HeaderCell>
            <Table.HeaderCell className="explorer-list-size">
              <LocalizedText source={"Size"} /></Table.HeaderCell>
            <Table.HeaderCell className="explorer-list-action" />
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {total === 0 ? (
            <Table.Row>
              <Table.Cell
                colSpan={99}
                style={{
                  opacity: 0.5,
                  padding: '10px !important',
                  textAlign: 'center',
                }}
              >
                <LocalizedText source={"No files or directories"} /></Table.Cell>
            </Table.Row>
          ) : (
            <>
              {subdirectory.length > 0 && (
                <DirectoryRow
                  deletable={false}
                  fullName=".."
                  name=".."
                onClick={upOneSubdirectory}
                remoteFileManagement={remoteFileManagement}
                root={root}
                subdirectory={subdirectory}
                />
              )}
              {directories.map((d) => (
                <DirectoryRow
                  key={d.name}
                  deleting={
                    deletingPath ===
                    'directory:' + fileStoragePath(subdirectory, d.fullName || d.name)
                  }
                  onClick={() => select({ path: d.name })}
                  onDelete={() =>
                    handleDelete({
                      kind: 'directory',
                      path: fileStoragePath(
                        subdirectory,
                        d.fullName || d.name,
                      ),
                    })
                  }
                  remoteFileManagement={remoteFileManagement}
                  root={root}
                  subdirectory={subdirectory}
                  {...d}
                />
              ))}
              {files.map((f) => (
                <FileRow
                  key={f.name}
                  deleting={
                    deletingPath ===
                    'file:' + fileStoragePath(subdirectory, f.fullName || f.name)
                  }
                  onDelete={() =>
                    handleDelete({
                      kind: 'file',
                      path: fileStoragePath(subdirectory, f.fullName || f.name),
                    })
                  }
                  remoteFileManagement={remoteFileManagement}
                  root={root}
                  subdirectory={subdirectory}
                  {...f}
                />
              ))}
            </>
          )}
        </Table.Body>
        </Table>
      )}
    </>
  );
};

export default Explorer;
