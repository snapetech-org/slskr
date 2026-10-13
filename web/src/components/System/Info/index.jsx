import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import { getVersion, restart, shutdown } from '../../../lib/application';
import DiagnosticBundleModal from './DiagnosticBundleModal';
import SetupHealthCheckModal from './SetupHealthCheckModal';
import { safeOpenBlank } from '../../../lib/safeOpen';
import {
  CodeEditor,
  LoaderSegment,
  ShrinkableButton,
  Switch,
} from '../../Shared';
import React, { useEffect, useState } from 'react';
import { Divider, Header, Modal } from 'semantic-ui-react';
import YAML from 'yaml';

const Info = ({ runtimeProfile, options, state, theme }) => {
  useInterfaceLanguage();
  const [contents, setContents] = useState();

  useEffect(() => {
    const timeout = setTimeout(() => {
      setContents(
        YAML.stringify(state, { simpleKeys: true, sortMapEntries: false }),
      );
    }, 250);

    return () => clearTimeout(timeout);
  }, [state]);

  const { pendingRestart } = state;

  return (
    <>
      <div className="header-buttons">
        <div style={{ float: 'left' }}>
          <ShrinkableButton
            disabled={!contents}
            icon="refresh"
            mediaQuery="(max-width: 686px)"
            onClick={() => getVersion({ forceCheck: true })}
            primary
          >
            <LocalizedText source={"Check for Updates"} /></ShrinkableButton>
          {/* Neutral, not amber — this is an optional external upsell from
              Soulseek itself, not an app action that needs to alarm anyone. */}
          <ShrinkableButton
            disabled={!contents}
            icon="star"
            mediaQuery="(max-width: 686px)"
            onClick={() =>
              safeOpenBlank(
                `http://www.slsknet.org/qtlogin.php?username=${encodeURIComponent(
                  state?.user?.username ?? '',
                )}`,
              )
            }
          >
            <LocalizedText source={"Get Privileges"} /></ShrinkableButton>
          {runtimeProfile !== 'legacy' && (
            <DiagnosticBundleModal
              options={options}
              state={state}
            />
          )}
          {runtimeProfile !== 'legacy' && (
            <SetupHealthCheckModal
              options={options}
              state={state}
            />
          )}
        </div>
        <Modal
          actions={[
            'Cancel',
            {
              content: interfaceText("Shut Down"),
              key: 'done',
              negative: true,
              onClick: shutdown,
            },
          ]}
          centered
          content={interfaceText("Are you sure you want to shut the application down? You'll need to manually start it again.")}
          header={
            <Header
              content={interfaceText("Confirm Shutdown")}
              icon="redo"
             {...interfaceTextProps("Confirm Shutdown")}/>
          }
          size="mini"
          trigger={
            <ShrinkableButton
              disabled={!contents}
              icon="shutdown"
              mediaQuery="(max-width: 686px)"
              negative
            >
              <LocalizedText source={"Shut Down"} /></ShrinkableButton>
          }
         {...interfaceTextProps("Are you sure you want to shut the application down? You'll need to manually start it again.")}/>
        <Modal
          actions={[
            'Cancel',
            {
              content: interfaceText("Restart"),
              key: 'done',
              negative: true,
              onClick: restart,
            },
          ]}
          centered
          content={interfaceText("Are you sure you want restart the application?")}
          header={
            <Header
              content={interfaceText("Confirm Restart")}
              icon="redo"
             {...interfaceTextProps("Confirm Restart")}/>
          }
          size="mini"
          trigger={
            <ShrinkableButton
              color={pendingRestart ? 'yellow' : undefined}
              disabled={!contents}
              icon="redo"
              mediaQuery="(max-width: 686px)"
              negative={!pendingRestart}
            >
              <LocalizedText source={"Restart"} /></ShrinkableButton>
          }
         {...interfaceTextProps("Are you sure you want restart the application?")}/>
      </div>
      <Divider />
      <Switch loading={!contents && <LoaderSegment />}>
        <CodeEditor
          ariaLabel={interfaceText("System information JSON")}
          basicSetup={false}
          editable={false}
          theme={theme}
          value={contents}
         {...interfaceTextProps("System information JSON")}/>
      </Switch>
    </>
  );
};

export default Info;
