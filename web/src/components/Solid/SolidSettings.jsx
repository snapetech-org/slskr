import LocalizedText from "../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import { toDisplayError } from '../../lib/errors';
import { useMountedRef } from '../../lib/useMountedRef';
import React, { useEffect, useRef, useState } from 'react';
import { TooltipButton } from '../Shared';
import { Form, Message, Segment } from 'semantic-ui-react';
import api from '../../lib/api';

export default function SolidSettings() {
  useInterfaceLanguage();
  const [status, setStatus] = useState(null);
  const [webId, setWebId] = useState('');
  const [resolved, setResolved] = useState(null);
  const [err, setErr] = useState('');
  const mountedRef = useMountedRef();
  const statusRequestIdRef = useRef(0);
  const resolveRequestIdRef = useRef(0);
  const resolveInFlightRef = useRef(false);
  const [resolving, setResolving] = useState(false);

  const formatError = (e) => {
    const data = e?.response?.data;
    if (typeof data === 'string' && data.trim().length > 0) return data;
    if (data != null && typeof data !== 'string') {
      try {
        return JSON.stringify(data);
      } catch {
        return String(data);
      }
    }
    return e?.message ?? String(e);
  };

  useEffect(() => {
    const requestId = ++statusRequestIdRef.current;
    (async () => {
      if (!mountedRef.current) return;
      setErr('');
      try {
        const res = await api.get('/solid/status');
        if (
          mountedRef.current &&
          statusRequestIdRef.current === requestId
        ) {
          setStatus(res.data);
        }
      } catch (e) {
        const statusCode = e?.response?.status;
        if (statusCode === 404) {
          if (
            mountedRef.current &&
            statusRequestIdRef.current === requestId
          ) {
            setStatus({ enabled: false });
          }
          return;
        }

        if (
          mountedRef.current &&
          statusRequestIdRef.current === requestId
        ) {
          setErr(toDisplayError(e, formatError(e)));
        }
      }
    })();

    return () => {
      statusRequestIdRef.current += 1;
    };
  }, [mountedRef]);

  const resolveWebId = async () => {
    const normalizedWebId = typeof webId === 'string' ? webId.trim() : '';
    if (!mountedRef.current || !normalizedWebId || resolveInFlightRef.current) return;
    const requestId = ++resolveRequestIdRef.current;
    const isCurrentRequest = () =>
      mountedRef.current && resolveRequestIdRef.current === requestId;
    setErr('');
    setResolved(null);
    resolveInFlightRef.current = true;
    setResolving(true);
    try {
      const res = await api.post('/solid/resolve-webid', { webId: normalizedWebId });
      if (isCurrentRequest()) setResolved(res.data);
    } catch (e) {
      if (isCurrentRequest()) setErr(toDisplayError(e, formatError(e)));
    } finally {
      resolveInFlightRef.current = false;
      if (mountedRef.current) setResolving(false);
    }
  };

  return (
    <Segment data-testid="solid-root">
      <h2><LocalizedText source={"Solid"} /></h2>

      {status && !status.enabled && (
        <Message warning>
          <LocalizedText source={"Solid integration is disabled (Feature.Solid=false)."} /></Message>
      )}

      {status && status.enabled && (
        <Message info>
          <LocalizedText source={"Client ID:"} />{" "}<code>{status.clientId}</code>
          <br />
          <LocalizedText source={"Redirect path:"} />{" "}<code>{status.redirectPath}</code>
        </Message>
      )}

      {err && <Message negative>{err}</Message>}

      <Form>
        <Form.Input
          label={interfaceText("WebID")}
          placeholder="https://example.com/profile/card#me"
          value={webId}
          onChange={(e) => setWebId(e.target.value)}
          data-testid="solid-webid-input"
         {...interfaceTextProps("WebID")}/>
        <TooltipButton
          primary
          type="button"
          disabled={resolving || !webId.trim()}
          loading={resolving}
          onClick={resolveWebId}
          data-testid="solid-resolve-webid"
          tooltip="Resolve this WebID and show the Solid identity document returned by the server."
        >
          <LocalizedText source={"Resolve WebID"} /></TooltipButton>
      </Form>

      {resolved && (
        <Segment>
          <pre style={{ whiteSpace: 'pre-wrap' }}>
            {JSON.stringify(resolved, null, 2)}
          </pre>
        </Segment>
      )}
    </Segment>
  );
}
