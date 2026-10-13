import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import {
  CodeEditor,
  LoaderSegment,
  ShrinkableButton,
  Switch,
} from '../../Shared';
import DebugModal from './DebugModal';
import EditModal from './EditModal';
import React, { useEffect, useState } from 'react';
import { Divider } from 'semantic-ui-react';
import YAML from 'yaml';

const DebugButton = ({
  debug,
  remoteConfiguration,
  setDebugModal,
  ...props
}) => {
  useInterfaceLanguage();
  if (!remoteConfiguration || !debug) return null;

  return (
    <ShrinkableButton
      icon="bug"
      mediaQuery="(max-width: 516px)"
      onClick={() => setDebugModal(true)}
      {...props}
    >
      <LocalizedText source={"Debug View"} /></ShrinkableButton>
  );
};

const EditButton = ({ remoteConfiguration, setEditModal, ...props }) => {
  useInterfaceLanguage();
  if (!remoteConfiguration) {
    return (
      <ShrinkableButton
        disabled
        icon="lock"
        mediaQuery="(max-width: 516px)"
      >
        <LocalizedText source={"Remote Configuration Disabled"} /></ShrinkableButton>
    );
  }

  return (
    <ShrinkableButton
      icon="edit"
      mediaQuery="(max-width: 516px)"
      onClick={() => setEditModal(true)}
      primary
      {...props}
    >
      <LocalizedText source={"Edit"} /></ShrinkableButton>
  );
};

const Options = ({ options, theme }) => {
  useInterfaceLanguage();
  const [debugModal, setDebugModal] = useState(false);
  const [editModal, setEditModal] = useState(false);
  const [contents, setContents] = useState();

  useEffect(() => {
    setContents(undefined);
    const timeout = setTimeout(() => {
      setContents(
        YAML.stringify(options, { simpleKeys: true, sortMapEntries: false }),
      );
    }, 250);

    return () => clearTimeout(timeout);
  }, [options]);

  const { debug, remoteConfiguration } = options;

  return (
    <>
      <div className="header-buttons">
        <DebugButton
          debug={debug}
          disabled={!contents}
          remoteConfiguration={remoteConfiguration}
          setDebugModal={setDebugModal}
        />
        <EditButton
          disabled={!contents}
          remoteConfiguration={remoteConfiguration}
          setEditModal={setEditModal}
        />
      </div>
      <Divider />
      <Switch loading={!contents && <LoaderSegment />}>
        <CodeEditor
          ariaLabel={interfaceText("Server options JSON")}
          basicSetup={false}
          editable={false}
          theme={theme}
          value={contents}
         {...interfaceTextProps("Server options JSON")}/>
      </Switch>
      <DebugModal
        onClose={() => setDebugModal(false)}
        open={debugModal}
        theme={theme}
      />
      <EditModal
        onClose={() => setEditModal(false)}
        open={editModal}
        theme={theme}
      />
    </>
  );
};

export default Options;
