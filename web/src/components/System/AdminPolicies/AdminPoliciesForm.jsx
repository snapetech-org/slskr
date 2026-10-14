import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps } from "../../../lib/interfaceLocale";
import React from 'react';
import {
  Button,
  Card,
  Checkbox,
  Form,
  Header,
  Icon,
  Label,
  Message,
  Popup,
  Segment,
  Table,
} from 'semantic-ui-react';

const boolLabel = (value, trueText = 'Enabled', falseText = 'Disabled') => (
  <Label color={value ? 'green' : 'grey'}>
    <Icon name={value ? 'check circle' : 'minus circle'} />
    {value ? trueText : falseText}
  </Label>
);

const AdminPoliciesForm = ({
  form,
  message,
  missing,
  remoteConfiguration,
  reset,
  saveYaml,
  saving,
  update,
}) => (
    <div className="admin-policies">
      <Segment>
        <Header as="h3">
          <Icon name="sliders horizontal" />
          <LocalizedText source={"Policies"} /></Header>
        <p>
          <LocalizedText source={"Guided YAML controls for operator policies that are otherwise easy to miss in raw configuration."} /></p>
      </Segment>

      {!remoteConfiguration && (
        <Message
          info
          size="small"
        >
          <LocalizedText source={"Remote configuration is disabled. These controls show the settings shape, but YAML saving is disabled until remote configuration is enabled."} /></Message>
      )}

      {message && (
        <Message
          negative={message.negative}
          positive={message.positive}
          size="small"
        >
          {message.text}
        </Message>
      )}
      {missing.length > 0 && (
        <Message
          size="small"
          warning
        >
          <Message.List items={missing} />
        </Message>
      )}

      <Card.Group
        itemsPerRow={1}
        stackable
      >
        <Card fluid>
          <Card.Content>
            <Card.Header>
              <Icon name="bolt" />
              <LocalizedText source={"Actions: Webhooks and Scripts"} /></Card.Header>
            <Card.Meta><LocalizedText source={"Event hooks, remote targets, command hooks, and retry shape."} /></Card.Meta>
          </Card.Content>
          <Card.Content>
            <Form>
              <Form.Group grouped>
                <Popup
                  content={interfaceText("Probe shared audio files for bitrate, duration, and sample metadata during share scans. Disable on slow or remote storage.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Probe share media attributes")}
                      checked={form.shareProbeMediaAttributes}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Probe share media attributes")}
                      onChange={(_, { checked }) =>
                        update('shareProbeMediaAttributes', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Probe share media attributes")}/>
                  }
                 {...interfaceTextProps("Probe shared audio files for bitrate, duration, and sample metadata during share scans. Disable on slow or remote storage.")}/>
              </Form.Group>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("Webhook policy name")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Webhook Name")}
                  onChange={(_, { value }) => update('webhookName', value)}
                  value={form.webhookName}
                 {...interfaceTextProps("Webhook policy name")}/>
                <Form.Input
                  aria-label={interfaceText("Webhook target URL")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Webhook URL")}
                  onChange={(_, { value }) => update('webhookUrl', value)}
                  placeholder="https://example.invalid/slskr-hook"
                  value={form.webhookUrl}
                 {...interfaceTextProps("Webhook target URL")}/>
                <Form.Input
                  aria-label={interfaceText("Webhook retry attempts")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Retry Attempts")}
                  min={1}
                  onChange={(_, { value }) => update('webhookRetryAttempts', value)}
                  type="number"
                  value={form.webhookRetryAttempts}
                 {...interfaceTextProps("Webhook retry attempts")}/>
                <Form.Input
                  aria-label={interfaceText("Webhook timeout milliseconds")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Timeout ms")}
                  min={1000}
                  onChange={(_, { value }) => update('webhookTimeout', value)}
                  type="number"
                  value={form.webhookTimeout}
                 {...interfaceTextProps("Webhook timeout milliseconds")}/>
              </Form.Group>
              <Form.TextArea
                aria-label={interfaceText("Webhook event names")}
                disabled={!remoteConfiguration || saving}
                label={interfaceText("Webhook Events")}
                onChange={(_, { value }) => update('webhookEvents', value)}
                placeholder={interfaceText("PrivateMessageReceived&#10;DownloadFileComplete")}
                value={form.webhookEvents}
               {...interfaceTextProps("Webhook event names")}/>
              <Popup
                content={interfaceText("Allow this webhook to call a target with a self-signed or otherwise untrusted certificate.")}
                trigger={
                  <Checkbox
                    aria-label={interfaceText("Ignore webhook certificate errors")}
                    checked={form.webhookIgnoreCertificateErrors}
                    disabled={!remoteConfiguration || saving}
                    label={interfaceText("Ignore webhook certificate errors")}
                    onChange={(_, { checked }) =>
                      update('webhookIgnoreCertificateErrors', Boolean(checked))
                    }
                    toggle
                   {...interfaceTextProps("Ignore webhook certificate errors")}/>
                }
               {...interfaceTextProps("Allow this webhook to call a target with a self-signed or otherwise untrusted certificate.")}/>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("Script policy name")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Script Name")}
                  onChange={(_, { value }) => update('scriptName', value)}
                  value={form.scriptName}
                 {...interfaceTextProps("Script policy name")}/>
                <Form.Input
                  aria-label={interfaceText("Script command")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Script Command")}
                  onChange={(_, { value }) => update('scriptCommand', value)}
                  placeholder="/usr/local/bin/slskr-hook"
                  value={form.scriptCommand}
                 {...interfaceTextProps("Script command")}/>
              </Form.Group>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("Script executable")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Script Executable")}
                  onChange={(_, { value }) => update('scriptExecutable', value)}
                  placeholder="/bin/sh"
                  value={form.scriptExecutable}
                 {...interfaceTextProps("Script executable")}/>
                <Form.Input
                  aria-label={interfaceText("Script arguments")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Script Args")}
                  onChange={(_, { value }) => update('scriptArgs', value)}
                  placeholder="-c ./hook.sh"
                  value={form.scriptArgs}
                 {...interfaceTextProps("Script arguments")}/>
              </Form.Group>
              <Form.TextArea
                aria-label={interfaceText("Script event names")}
                disabled={!remoteConfiguration || saving}
                label={interfaceText("Script Events")}
                onChange={(_, { value }) => update('scriptEvents', value)}
                placeholder={interfaceText("DownloadFileComplete")}
                value={form.scriptEvents}
               {...interfaceTextProps("Script event names")}/>
            </Form>
          </Card.Content>
        </Card>

        <Card fluid>
          <Card.Content>
            <Card.Header>
              <Icon name="exchange" />
              <LocalizedText source={"Transfer Policy"} /></Card.Header>
            <Card.Meta><LocalizedText source={"Slots, speed ceilings, auto-replace, and schedule enablement."} /></Card.Meta>
          </Card.Content>
          <Card.Content>
            <div className="integration-status-row">
              {boolLabel(form.scheduledLimitsEnabled, 'Schedules On', 'Schedules Off')}
              {boolLabel(form.autoReplaceStuck, 'Auto-Replace On', 'Auto-Replace Off')}
            </div>
            <Form>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("Global upload slots")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Upload Slots")}
                  onChange={(_, { value }) => update('uploadSlots', value)}
                  type="number"
                  value={form.uploadSlots}
                 {...interfaceTextProps("Global upload slots")}/>
                <Form.Input
                  aria-label={interfaceText("Global upload speed limit")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Upload KiB/s")}
                  onChange={(_, { value }) => update('uploadSpeedLimit', value)}
                  type="number"
                  value={form.uploadSpeedLimit}
                 {...interfaceTextProps("Global upload speed limit")}/>
                <Form.Input
                  aria-label={interfaceText("Global download slots")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Download Slots")}
                  onChange={(_, { value }) => update('downloadSlots', value)}
                  type="number"
                  value={form.downloadSlots}
                 {...interfaceTextProps("Global download slots")}/>
                <Form.Input
                  aria-label={interfaceText("Global download speed limit")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Download KiB/s")}
                  onChange={(_, { value }) => update('downloadSpeedLimit', value)}
                  type="number"
                  value={form.downloadSpeedLimit}
                 {...interfaceTextProps("Global download speed limit")}/>
              </Form.Group>
              <Form.Group widths="equal">
                <Form.Select
                  aria-label={interfaceText("Download retry incomplete strategy")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Retry Partial Files")}
                  onChange={(_, { value }) => update('downloadRetryIncomplete', value)}
                  options={[
                    { key: 'resume', text: interfaceText("resume"), value: 'resume' },
                    { key: 'overwrite', text: interfaceText("overwrite"), value: 'overwrite' },
                  ]}
                  value={form.downloadRetryIncomplete}
                 {...interfaceTextProps("Download retry incomplete strategy")}/>
                <Form.Input
                  aria-label={interfaceText("Download retry attempts")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Retry Attempts")}
                  min={1}
                  onChange={(_, { value }) => update('downloadRetryAttempts', value)}
                  type="number"
                  value={form.downloadRetryAttempts}
                 {...interfaceTextProps("Download retry attempts")}/>
                <Form.Input
                  aria-label={interfaceText("Download retry delay milliseconds")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Retry Delay ms")}
                  min={0}
                  onChange={(_, { value }) => update('downloadRetryDelay', value)}
                  type="number"
                  value={form.downloadRetryDelay}
                 {...interfaceTextProps("Download retry delay milliseconds")}/>
                <Form.Input
                  aria-label={interfaceText("Download retry max delay milliseconds")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Retry Max Delay ms")}
                  min={1000}
                  onChange={(_, { value }) => update('downloadRetryMaxDelay', value)}
                  type="number"
                  value={form.downloadRetryMaxDelay}
                 {...interfaceTextProps("Download retry max delay milliseconds")}/>
              </Form.Group>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("Auto replace interval seconds")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Auto-Replace Interval")}
                  min={60}
                  onChange={(_, { value }) => update('autoReplaceInterval', value)}
                  type="number"
                  value={form.autoReplaceInterval}
                 {...interfaceTextProps("Auto replace interval seconds")}/>
                <Form.Input
                  aria-label={interfaceText("Auto replace size threshold")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Size Threshold %")}
                  min={0}
                  onChange={(_, { value }) => update('autoReplaceThreshold', value)}
                  type="number"
                  value={form.autoReplaceThreshold}
                 {...interfaceTextProps("Auto replace size threshold")}/>
                <Form.Input
                  aria-label={interfaceText("Auto replace max retries")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Max Retries")}
                  min={0}
                  onChange={(_, { value }) => update('autoReplaceMaxRetries', value)}
                  type="number"
                  value={form.autoReplaceMaxRetries}
                 {...interfaceTextProps("Auto replace max retries")}/>
              </Form.Group>
              <Form.Group grouped>
                <Popup
                  content={interfaceText("Enable automatic replacement of stuck downloads with alternative sources.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Enable auto replace stuck downloads")}
                      checked={form.autoReplaceStuck}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Enable auto-replace stuck downloads")}
                      onChange={(_, { checked }) =>
                        update('autoReplaceStuck', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Enable auto replace stuck downloads")}/>
                  }
                 {...interfaceTextProps("Enable automatic replacement of stuck downloads with alternative sources.")}/>
                <Popup
                  content={interfaceText("Enable the legacy top-level scheduled speed-limit policy in YAML.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Enable scheduled speed limits")}
                      checked={form.scheduledLimitsEnabled}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Enable scheduled speed limits")}
                      onChange={(_, { checked }) =>
                        update('scheduledLimitsEnabled', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Enable scheduled speed limits")}/>
                  }
                 {...interfaceTextProps("Enable the legacy top-level scheduled speed-limit policy in YAML.")}/>
                <Popup
                  content={interfaceText("Enable scheduled upload speed limits under global upload policy.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Enable upload scheduled speed limits")}
                      checked={form.uploadScheduledLimitsEnabled}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Enable upload schedules")}
                      onChange={(_, { checked }) =>
                        update('uploadScheduledLimitsEnabled', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Enable upload scheduled speed limits")}/>
                  }
                 {...interfaceTextProps("Enable scheduled upload speed limits under global upload policy.")}/>
                <Popup
                  content={interfaceText("Enable scheduled download speed limits under global download policy.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Enable download scheduled speed limits")}
                      checked={form.downloadScheduledLimitsEnabled}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Enable download schedules")}
                      onChange={(_, { checked }) =>
                        update('downloadScheduledLimitsEnabled', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Enable download scheduled speed limits")}/>
                  }
                 {...interfaceTextProps("Enable scheduled download speed limits under global download policy.")}/>
              </Form.Group>
            </Form>
          </Card.Content>
        </Card>

        <Card fluid>
          <Card.Content>
            <Card.Header>
              <Icon name="lock" />
              <LocalizedText source={"Security and Access"} /></Card.Header>
            <Card.Meta><LocalizedText source={"Authentication, API keys, HTTPS, CORS-adjacent rate limits, and restart cues."} /></Card.Meta>
          </Card.Content>
          <Card.Content>
            <div className="integration-status-row">
              {boolLabel(!form.noAuth, 'Auth On', 'No Auth')}
              {boolLabel(form.jwtConfigured, 'JWT Key Set', 'JWT Key Missing')}
              {boolLabel(form.apiKeyConfigured, 'API Key Set', 'API Key Missing')}
              {boolLabel(!form.httpsDisabled, 'HTTPS On', 'HTTPS Off')}
              {boolLabel(
                form.httpsCertificatePasswordConfigured,
                'Certificate Password Set',
                'Certificate Password Missing',
              )}
            </div>
            <Form>
              <Form.Group grouped>
                <Popup
                  content={interfaceText("Enable strict startup and request hardening checks for exposed deployments.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Enforce web security hardening")}
                      checked={form.enforceSecurity}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Enforce security hardening")}
                      onChange={(_, { checked }) =>
                        update('enforceSecurity', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Enforce web security hardening")}/>
                  }
                 {...interfaceTextProps("Enable strict startup and request hardening checks for exposed deployments.")}/>
                <Popup
                  content={interfaceText("Disable Web UI authentication only for tightly controlled loopback deployments.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Disable web authentication")}
                      checked={form.noAuth}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Disable authentication")}
                      onChange={(_, { checked }) => update('noAuth', Boolean(checked))}
                      toggle
                     {...interfaceTextProps("Disable web authentication")}/>
                  }
                 {...interfaceTextProps("Disable Web UI authentication only for tightly controlled loopback deployments.")}/>
                <Popup
                  content={interfaceText("Allow no-auth access from explicitly configured non-loopback CIDRs.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Allow remote no-auth CIDRs")}
                      checked={form.allowRemoteNoAuth}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Allow remote no-auth CIDRs")}
                      onChange={(_, { checked }) =>
                        update('allowRemoteNoAuth', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Allow remote no-auth CIDRs")}/>
                  }
                 {...interfaceTextProps("Allow no-auth access from explicitly configured non-loopback CIDRs.")}/>
                <Popup
                  content={interfaceText("Enable HTTP rate limiting for API, federation, and mesh gateway policies.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Enable HTTP rate limiting")}
                      checked={form.rateLimitEnabled}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Enable HTTP rate limiting")}
                      onChange={(_, { checked }) =>
                        update('rateLimitEnabled', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Enable HTTP rate limiting")}/>
                  }
                 {...interfaceTextProps("Enable HTTP rate limiting for API, federation, and mesh gateway policies.")}/>
              </Form.Group>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("JWT replacement key")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("JWT Key")}
                  onChange={(_, { value }) => update('jwtKey', value)}
                  placeholder={form.jwtConfigured ? 'Configured' : 'New JWT key'}
                  type="password"
                  value={form.jwtKey}
                 {...interfaceTextProps("JWT replacement key")}/>
                <Form.Input
                  aria-label={interfaceText("JWT TTL milliseconds")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("JWT TTL ms")}
                  min={3600}
                  onChange={(_, { value }) => update('jwtTtl', value)}
                  type="number"
                  value={form.jwtTtl}
                 {...interfaceTextProps("JWT TTL milliseconds")}/>
                <Form.Input
                  aria-label={interfaceText("No auth allowed CIDRs")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("No-Auth CIDRs")}
                  onChange={(_, { value }) => update('passthroughCidrs', value)}
                  value={form.passthroughCidrs}
                 {...interfaceTextProps("No auth allowed CIDRs")}/>
              </Form.Group>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("API key policy name")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("API Key Name")}
                  onChange={(_, { value }) => update('apiKeyName', value)}
                  value={form.apiKeyName}
                 {...interfaceTextProps("API key policy name")}/>
                <Form.Input
                  aria-label={interfaceText("API key replacement value")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("API Key")}
                  onChange={(_, { value }) => update('apiKeyValue', value)}
                  placeholder={form.apiKeyConfigured ? 'Configured' : 'New API key'}
                  type="password"
                  value={form.apiKeyValue}
                 {...interfaceTextProps("API key replacement value")}/>
                <Form.Select
                  aria-label={interfaceText("API key role")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Role")}
                  onChange={(_, { value }) => update('apiKeyRole', value)}
                  options={[
                    { key: 'ReadOnly', text: interfaceText("ReadOnly"), value: 'ReadOnly' },
                    { key: 'ReadWrite', text: interfaceText("ReadWrite"), value: 'ReadWrite' },
                    {
                      key: 'Administrator',
                      text: interfaceText("Administrator"),
                      value: 'Administrator',
                    },
                  ]}
                  value={form.apiKeyRole}
                 {...interfaceTextProps("API key role")}/>
              </Form.Group>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("API key CIDR allowlist")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("API CIDRs")}
                  onChange={(_, { value }) => update('apiKeyCidr', value)}
                  value={form.apiKeyCidr}
                 {...interfaceTextProps("API key CIDR allowlist")}/>
                <Form.Input
                  aria-label={interfaceText("API key scopes")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("API Scopes")}
                  onChange={(_, { value }) => update('apiKeyScopes', value)}
                  value={form.apiKeyScopes}
                 {...interfaceTextProps("API key scopes")}/>
              </Form.Group>
              <Form.Group grouped>
                <Popup
                  content={interfaceText("Disable HTTPS listener. Keep this off when exposing the Web UI beyond localhost.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Disable HTTPS listener")}
                      checked={form.httpsDisabled}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Disable HTTPS")}
                      onChange={(_, { checked }) =>
                        update('httpsDisabled', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Disable HTTPS listener")}/>
                  }
                 {...interfaceTextProps("Disable HTTPS listener. Keep this off when exposing the Web UI beyond localhost.")}/>
                <Popup
                  content={interfaceText("Redirect HTTP requests to HTTPS after certificate settings are valid.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Force HTTPS redirects")}
                      checked={form.forceHttps}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Force HTTPS")}
                      onChange={(_, { checked }) =>
                        update('forceHttps', Boolean(checked))
                      }
                     {...interfaceTextProps("Force HTTPS redirects")}/>
                  }
                 {...interfaceTextProps("Redirect HTTP requests to HTTPS after certificate settings are valid.")}/>
              </Form.Group>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("HTTPS port")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("HTTPS Port")}
                  onChange={(_, { value }) => update('httpsPort', value)}
                  type="number"
                  value={form.httpsPort}
                 {...interfaceTextProps("HTTPS port")}/>
                <Form.Input
                  aria-label={interfaceText("HTTPS certificate PFX path")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Certificate PFX (optional)")}
                  onChange={(_, { value }) => update('httpsCertificatePfx', value)}
                  value={form.httpsCertificatePfx}
                 {...interfaceTextProps("HTTPS certificate PFX path")}/>
                <Form.Input
                  aria-label={interfaceText("HTTPS certificate password")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Certificate Password")}
                  onChange={(_, { value }) =>
                    update('httpsCertificatePassword', value)
                  }
                  placeholder={
                    form.httpsCertificatePasswordConfigured
                      ? 'Configured'
                      : 'Certificate password'
                  }
                  type="password"
                  value={form.httpsCertificatePassword}
                 {...interfaceTextProps("HTTPS certificate password")}/>
              </Form.Group>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("API rate limit permits")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("API Permits/min")}
                  onChange={(_, { value }) => update('rateLimitApi', value)}
                  type="number"
                  value={form.rateLimitApi}
                 {...interfaceTextProps("API rate limit permits")}/>
                <Form.Input
                  aria-label={interfaceText("API rate limit window seconds")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("API Window sec")}
                  onChange={(_, { value }) => update('rateLimitApiWindow', value)}
                  type="number"
                  value={form.rateLimitApiWindow}
                 {...interfaceTextProps("API rate limit window seconds")}/>
                <Form.Input
                  aria-label={interfaceText("Federation rate limit permits")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Federation Permits/min")}
                  onChange={(_, { value }) => update('rateLimitFederation', value)}
                  type="number"
                  value={form.rateLimitFederation}
                 {...interfaceTextProps("Federation rate limit permits")}/>
                <Form.Input
                  aria-label={interfaceText("Federation rate limit window seconds")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Federation Window sec")}
                  onChange={(_, { value }) =>
                    update('rateLimitFederationWindow', value)
                  }
                  type="number"
                  value={form.rateLimitFederationWindow}
                 {...interfaceTextProps("Federation rate limit window seconds")}/>
              </Form.Group>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("Mesh gateway rate limit permits")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Mesh Permits/min")}
                  onChange={(_, { value }) => update('rateLimitMesh', value)}
                  type="number"
                  value={form.rateLimitMesh}
                 {...interfaceTextProps("Mesh gateway rate limit permits")}/>
                <Form.Input
                  aria-label={interfaceText("Mesh gateway rate limit window seconds")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Mesh Window sec")}
                  onChange={(_, { value }) => update('rateLimitMeshWindow', value)}
                  type="number"
                  value={form.rateLimitMeshWindow}
                 {...interfaceTextProps("Mesh gateway rate limit window seconds")}/>
              </Form.Group>
            </Form>
          </Card.Content>
        </Card>

        <Card fluid>
          <Card.Content>
            <Card.Header>
              <Icon name="sitemap" />
              <LocalizedText source={"Search and Network Policy"} /></Card.Header>
            <Card.Meta><LocalizedText source={"Incoming search throttles, request filters, and managed blacklist setup."} /></Card.Meta>
          </Card.Content>
          <Card.Content>
            <div className="integration-status-row">
              {boolLabel(form.blacklistEnabled, 'Blacklist On', 'Blacklist Off')}
              {boolLabel(form.dhtEnabled, 'DHT On', 'DHT Off')}
              {boolLabel(form.dhtLanOnly, 'LAN Only', 'Public DHT')}
              {boolLabel(form.featureScenePodBridge, 'Bridge On', 'Bridge Off')}
              {boolLabel(form.rescueModeEnabled, 'Rescue On', 'Rescue Off')}
            </div>
            <Form>
              <Form.TextArea
                aria-label={interfaceText("Incoming search request filters")}
                disabled={!remoteConfiguration || saving}
                label={interfaceText("Incoming Search Filter Regexes")}
                onChange={(_, { value }) => update('searchFilterRequest', value)}
                placeholder="(?i)forbidden term"
                value={form.searchFilterRequest}
               {...interfaceTextProps("Incoming search request filters")}/>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("Incoming search concurrency")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Incoming Concurrency")}
                  onChange={(_, { value }) =>
                    update('searchIncomingConcurrency', value)
                  }
                  type="number"
                  value={form.searchIncomingConcurrency}
                 {...interfaceTextProps("Incoming search concurrency")}/>
                <Form.Input
                  aria-label={interfaceText("Incoming search circuit breaker")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Circuit Breaker")}
                  onChange={(_, { value }) =>
                    update('searchIncomingCircuitBreaker', value)
                  }
                  type="number"
                  value={form.searchIncomingCircuitBreaker}
                 {...interfaceTextProps("Incoming search circuit breaker")}/>
                <Form.Input
                  aria-label={interfaceText("Incoming search response file limit")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Response File Limit")}
                  onChange={(_, { value }) =>
                    update('searchIncomingResponseFileLimit', value)
                  }
                  type="number"
                  value={form.searchIncomingResponseFileLimit}
                 {...interfaceTextProps("Incoming search response file limit")}/>
              </Form.Group>
              <Form.Group widths="equal">
                <Popup
                  content={interfaceText("Enable loading a managed CIDR/P2P/DAT blacklist file at startup.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Enable managed blacklist")}
                      checked={form.blacklistEnabled}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Enable managed blacklist")}
                      onChange={(_, { checked }) =>
                        update('blacklistEnabled', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Enable managed blacklist")}/>
                  }
                 {...interfaceTextProps("Enable loading a managed CIDR/P2P/DAT blacklist file at startup.")}/>
                <Form.Input
                  aria-label={interfaceText("Managed blacklist file path")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Blacklist File")}
                  onChange={(_, { value }) => update('blacklistFile', value)}
                  value={form.blacklistFile}
                 {...interfaceTextProps("Managed blacklist file path")}/>
              </Form.Group>
              <Form.Group grouped>
                <Popup
                  content={interfaceText("Enable DHT rendezvous. Disable this when you want no DHT peer discovery.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Enable DHT rendezvous")}
                      checked={form.dhtEnabled}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Enable DHT rendezvous")}
                      onChange={(_, { checked }) =>
                        update('dhtEnabled', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Enable DHT rendezvous")}/>
                  }
                 {...interfaceTextProps("Enable DHT rendezvous. Disable this when you want no DHT peer discovery.")}/>
                <Popup
                  content={interfaceText("Keep DHT discovery away from public bootstrap routers and use only private or local discovery paths.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Use LAN-only DHT rendezvous")}
                      checked={form.dhtLanOnly}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("LAN-only DHT")}
                      onChange={(_, { checked }) =>
                        update('dhtLanOnly', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Use LAN-only DHT rendezvous")}/>
                  }
                 {...interfaceTextProps("Keep DHT discovery away from public bootstrap routers and use only private or local discovery paths.")}/>
                <Popup
                  content={interfaceText("Opt in to experimental Scene and Pod bridge aggregation.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Enable Scene Pod Bridge")}
                      checked={form.featureScenePodBridge}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Enable Scene Pod Bridge")}
                      onChange={(_, { checked }) =>
                        update('featureScenePodBridge', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Enable Scene Pod Bridge")}/>
                  }
                 {...interfaceTextProps("Opt in to experimental Scene and Pod bridge aggregation.")}/>
                <Popup
                  content={interfaceText("Enable underperformance rescue policies for queued or stalled downloads.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Enable rescue mode")}
                      checked={form.rescueModeEnabled}
                      disabled={!remoteConfiguration || saving}
                      label={interfaceText("Enable rescue mode")}
                      onChange={(_, { checked }) =>
                        update('rescueModeEnabled', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Enable rescue mode")}/>
                  }
                 {...interfaceTextProps("Enable underperformance rescue policies for queued or stalled downloads.")}/>
              </Form.Group>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("DHT overlay TCP port")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Overlay TCP Port")}
                  onChange={(_, { value }) => update('dhtOverlayPort', value)}
                  type="number"
                  value={form.dhtOverlayPort}
                 {...interfaceTextProps("DHT overlay TCP port")}/>
                <Form.Input
                  aria-label={interfaceText("DHT UDP port")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("DHT UDP Port")}
                  onChange={(_, { value }) => update('dhtPort', value)}
                  type="number"
                  value={form.dhtPort}
                 {...interfaceTextProps("DHT UDP port")}/>
                <Form.Input
                  aria-label={interfaceText("DHT announce interval seconds")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("DHT Announce sec")}
                  onChange={(_, { value }) =>
                    update('dhtAnnounceIntervalSeconds', value)
                  }
                  type="number"
                  value={form.dhtAnnounceIntervalSeconds}
                 {...interfaceTextProps("DHT announce interval seconds")}/>
                <Form.Input
                  aria-label={interfaceText("Rescue max queue seconds")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Rescue Queue sec")}
                  onChange={(_, { value }) =>
                    update('rescueModeMaxQueueSeconds', value)
                  }
                  type="number"
                  value={form.rescueModeMaxQueueSeconds}
                 {...interfaceTextProps("Rescue max queue seconds")}/>
              </Form.Group>
              <Form.TextArea
                aria-label={interfaceText("DHT bootstrap routers")}
                disabled={!remoteConfiguration || saving}
                label={interfaceText("DHT Bootstrap Routers")}
                onChange={(_, { value }) => update('dhtBootstrapRouters', value)}
                placeholder="router.bittorrent.com"
                value={form.dhtBootstrapRouters}
               {...interfaceTextProps("DHT bootstrap routers")}/>
            </Form>
          </Card.Content>
        </Card>

        <Card fluid>
          <Card.Content>
            <Card.Header>
              <Icon name="archive" />
              <LocalizedText source={"Retention and Storage"} /></Card.Header>
            <Card.Meta><LocalizedText source={"Search/event/log cleanup, transfer history, file records, and share cache pressure."} /></Card.Meta>
          </Card.Content>
          <Card.Content>
            <Form>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("Search retention minutes")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Search Retention min")}
                  onChange={(_, { value }) => update('retentionSearch', value)}
                  value={form.retentionSearch}
                 {...interfaceTextProps("Search retention minutes")}/>
                <Form.Input
                  aria-label={interfaceText("Event retention days")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Events Retention days")}
                  onChange={(_, { value }) => update('eventsRetention', value)}
                  type="number"
                  value={form.eventsRetention}
                 {...interfaceTextProps("Event retention days")}/>
                <Form.Input
                  aria-label={interfaceText("Log retention days")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Logs Retention days")}
                  onChange={(_, { value }) => update('logRetention', value)}
                  type="number"
                  value={form.logRetention}
                 {...interfaceTextProps("Log retention days")}/>
              </Form.Group>
              <Table
                celled
                compact
              >
                <Table.Header>
                  <Table.Row>
                    <Table.HeaderCell><LocalizedText source={"History"} /></Table.HeaderCell>
                    <Table.HeaderCell><LocalizedText source={"Succeeded"} /></Table.HeaderCell>
                    <Table.HeaderCell><LocalizedText source={"Errored"} /></Table.HeaderCell>
                    <Table.HeaderCell><LocalizedText source={"Cancelled"} /></Table.HeaderCell>
                  </Table.Row>
                </Table.Header>
                <Table.Body>
                  <Table.Row>
                    <Table.Cell><LocalizedText source={"Uploads"} /></Table.Cell>
                    <Table.Cell>
                      <Form.Input
                        aria-label={interfaceText("Upload succeeded retention minutes")}
                        disabled={!remoteConfiguration || saving}
                        onChange={(_, { value }) =>
                          update('retentionUploadSucceeded', value)
                        }
                        value={form.retentionUploadSucceeded}
                       {...interfaceTextProps("Upload succeeded retention minutes")}/>
                    </Table.Cell>
                    <Table.Cell>
                      <Form.Input
                        aria-label={interfaceText("Upload errored retention minutes")}
                        disabled={!remoteConfiguration || saving}
                        onChange={(_, { value }) =>
                          update('retentionUploadErrored', value)
                        }
                        value={form.retentionUploadErrored}
                       {...interfaceTextProps("Upload errored retention minutes")}/>
                    </Table.Cell>
                    <Table.Cell>
                      <Form.Input
                        aria-label={interfaceText("Upload cancelled retention minutes")}
                        disabled={!remoteConfiguration || saving}
                        onChange={(_, { value }) =>
                          update('retentionUploadCancelled', value)
                        }
                        value={form.retentionUploadCancelled}
                       {...interfaceTextProps("Upload cancelled retention minutes")}/>
                    </Table.Cell>
                  </Table.Row>
                  <Table.Row>
                    <Table.Cell><LocalizedText source={"Downloads"} /></Table.Cell>
                    <Table.Cell>
                      <Form.Input
                        aria-label={interfaceText("Download succeeded retention minutes")}
                        disabled={!remoteConfiguration || saving}
                        onChange={(_, { value }) =>
                          update('retentionDownloadSucceeded', value)
                        }
                        value={form.retentionDownloadSucceeded}
                       {...interfaceTextProps("Download succeeded retention minutes")}/>
                    </Table.Cell>
                    <Table.Cell>
                      <Form.Input
                        aria-label={interfaceText("Download errored retention minutes")}
                        disabled={!remoteConfiguration || saving}
                        onChange={(_, { value }) =>
                          update('retentionDownloadErrored', value)
                        }
                        value={form.retentionDownloadErrored}
                       {...interfaceTextProps("Download errored retention minutes")}/>
                    </Table.Cell>
                    <Table.Cell>
                      <Form.Input
                        aria-label={interfaceText("Download cancelled retention minutes")}
                        disabled={!remoteConfiguration || saving}
                        onChange={(_, { value }) =>
                          update('retentionDownloadCancelled', value)
                        }
                        value={form.retentionDownloadCancelled}
                       {...interfaceTextProps("Download cancelled retention minutes")}/>
                    </Table.Cell>
                  </Table.Row>
                </Table.Body>
              </Table>
              <Form.Group widths="equal">
                <Form.Input
                  aria-label={interfaceText("Complete file retention minutes")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Complete Files min")}
                  onChange={(_, { value }) => update('fileCompleteRetention', value)}
                  value={form.fileCompleteRetention}
                 {...interfaceTextProps("Complete file retention minutes")}/>
                <Form.Input
                  aria-label={interfaceText("Incomplete file retention minutes")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Incomplete Files min")}
                  onChange={(_, { value }) =>
                    update('fileIncompleteRetention', value)
                  }
                  value={form.fileIncompleteRetention}
                 {...interfaceTextProps("Incomplete file retention minutes")}/>
                <Form.Input
                  aria-label={interfaceText("Share cache workers")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Share Cache Workers")}
                  onChange={(_, { value }) => update('shareCacheWorkers', value)}
                  type="number"
                  value={form.shareCacheWorkers}
                 {...interfaceTextProps("Share cache workers")}/>
                <Form.Input
                  aria-label={interfaceText("Share cache retention minutes")}
                  disabled={!remoteConfiguration || saving}
                  label={interfaceText("Share Cache Retention min")}
                  onChange={(_, { value }) => update('shareCacheRetention', value)}
                  value={form.shareCacheRetention}
                 {...interfaceTextProps("Share cache retention minutes")}/>
              </Form.Group>
            </Form>
          </Card.Content>
        </Card>
      </Card.Group>

      <div className="integration-actions admin-policy-actions">
        <Popup
          content={interfaceText("Persist the policy settings above to YAML. This does not test webhooks, run scripts, contact peers, restart the daemon, or mutate downloads.")}
          trigger={
            <Button
              disabled={!remoteConfiguration || missing.length > 0}
              icon
              labelPosition="left"
              loading={saving}
              onClick={saveYaml}
              primary
            >
              <Icon name="file alternate" />
              <LocalizedText source={"Save YAML"} /></Button>
          }
         {...interfaceTextProps("Persist the policy settings above to YAML. This does not test webhooks, run scripts, contact peers, restart the daemon, or mutate downloads.")}/>
        <Popup
          content={interfaceText("Discard unsaved policy edits and restore values currently reported by the daemon.")}
          trigger={
            <Button
              disabled={saving}
              icon
              labelPosition="left"
              onClick={reset}
            >
              <Icon name="undo" />
              <LocalizedText source={"Reset"} /></Button>
          }
         {...interfaceTextProps("Discard unsaved policy edits and restore values currently reported by the daemon.")}/>
      </div>
    </div>
);

export default AdminPoliciesForm;
