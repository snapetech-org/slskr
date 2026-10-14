import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";


import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import React, { useEffect, useRef } from 'react';
import ResolveExternalIdPanel from './ResolveExternalIdPanel';
import {
  contentExamples,
} from './mediaCoreWorkflows';
import {
  Card,
  Form,
  Grid,
  Header,
  Icon,
  Input,
  List,
  Message,
  Segment,
} from 'semantic-ui-react';

const useMountedState = (mountedRef, initialValue) => {
  const [value, setValue] = React.useState(initialValue);
  const setMountedValue = React.useCallback(
    (nextValue) => {
      if (mountedRef.current) {
        setValue(nextValue);
      }
    },
    [mountedRef],
  );

  return [value, setMountedValue];
};

const MediaCoreContentRegistryPanel = ({ setContentId, setError, setStats }) => {
  useInterfaceLanguage();
  const mountedRef = useRef(true);
  const resolveExternalIdPanelRef = useRef(null);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const [externalId, setExternalId] = useMountedState(mountedRef, '');
  const [descriptorContentId, setDescriptorContentId] = useMountedState(mountedRef, '');
  const [validateContentIdInput, setValidateContentIdInput] = useMountedState(mountedRef, '');
  const [domain, setDomain] = useMountedState(mountedRef, '');
  const [type, setType] = useMountedState(mountedRef, '');
  const [validatedContent, setValidatedContent] = useMountedState(mountedRef, null);
  const [domainResults, setDomainResults] = useMountedState(mountedRef, null);
  const [registering, setRegistering] = useMountedState(mountedRef, false);
  const [validating, setValidating] = useMountedState(mountedRef, false);
  const [searchingDomain, setSearchingDomain] = useMountedState(mountedRef, false);

  const handleRegister = async () => {
    if (!externalId.trim() || !descriptorContentId.trim()) return;

    try {
      setRegistering(true);
      await mediacore.registerContentId(
        externalId.trim(),
        descriptorContentId.trim(),
      );
      setExternalId('');
      setDescriptorContentId('');
      setContentId('');

      // Refresh stats
      const data = await mediacore.getContentIdStats();
      setStats(data);
    } catch (error_) {
      setError(interfaceText('Registration failed: {message}', { message: toDisplayError(error_) }));
    } finally {
      setRegistering(false);
    }
  };

  const handleValidate = async () => {
    if (!validateContentIdInput.trim()) return;

    try {
      setValidating(true);
      setValidatedContent(null);
      const result = await mediacore.validateContentId(
        validateContentIdInput.trim(),
      );
      setValidatedContent(result);
    } catch (error_) {
      setValidatedContent({ error: toDisplayError(error_) });
    } finally {
      setValidating(false);
    }
  };

  const handleDomainSearch = async () => {
    if (!domain.trim()) return;

    try {
      setSearchingDomain(true);
      setDomainResults(null);
      const result = type.trim()
        ? await mediacore.findContentIdsByDomainAndType(
            domain.trim(),
            type.trim(),
          )
        : await mediacore.findContentIdsByDomain(domain.trim());
      setDomainResults(result);
    } catch (error_) {
      setDomainResults({ error: toDisplayError(error_) });
    } finally {
      setSearchingDomain(false);
    }
  };

  const fillExample = (domain, type) => {
    const example = contentExamples[domain]?.[type];
    if (example) {
      setExternalId(example.external);
      resolveExternalIdPanelRef.current?.setQuery(example.external);
      setDescriptorContentId(example.content);
      setValidateContentIdInput(example.content);
    }
  };

  return (
    <>
        {/* Register New Mapping */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="plus" />
                <LocalizedText source={"Register ContentID Mapping"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Map an external identifier to an internal ContentID"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Field>
                  <label><LocalizedText source={"External ID"} /></label>
                  <Input
                    onChange={(e) => setExternalId(e.target.value)}
                    placeholder={interfaceText("e.g., mb:recording:12345-6789-...")}
                    value={externalId}
                   {...interfaceTextProps("e.g., mb:recording:12345-6789-...")}/>
                </Form.Field>
                <Form.Field>
                  <label><LocalizedText source={"Content ID"} /></label>
                  <Input
                    onChange={(e) => setDescriptorContentId(e.target.value)}
                    placeholder={interfaceText("e.g., content:mb:recording:12345-6789-...")}
                    value={descriptorContentId}
                   {...interfaceTextProps("e.g., content:mb:recording:12345-6789-...")}/>
                </Form.Field>
                <Button
                  disabled={
                    !externalId.trim() ||
                    !descriptorContentId.trim() ||
                    registering
                  }
                  loading={registering}
                  onClick={handleRegister}
                  primary
                >
                  <LocalizedText source={"Register Mapping"} /></Button>
              </Form>
            </Card.Content>
          </Card>
        </Grid.Column>

        <ResolveExternalIdPanel ref={resolveExternalIdPanelRef} />

        {/* ContentID Validation */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="check circle" />
                <LocalizedText source={"ContentID Validation"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Validate ContentID format and extract components"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Field>
                  <label><LocalizedText source={"ContentID to Validate"} /></label>
                  <Input
                    action={
                      <Button
                        disabled={!validateContentIdInput.trim() || validating}
                        loading={validating}
                        onClick={handleValidate}
                        primary
                      >
                        <LocalizedText source={"Validate"} /></Button>
                    }
                    onChange={(e) => setValidateContentIdInput(e.target.value)}
                    placeholder={interfaceText("e.g., content:audio:track:mb-12345")}
                    value={validateContentIdInput}
                   {...interfaceTextProps("e.g., content:audio:track:mb-12345")}/>
                </Form.Field>
              </Form>

              {validatedContent && (
                <div style={{ marginTop: '1em' }}>
                  {validatedContent.error ? (
                    <Message error>
                      <p>{validatedContent.error}</p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header><LocalizedText source={"Valid ContentID"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Domain:"} /></strong> {validatedContent.domain}
                        <br />
                        <strong><LocalizedText source={"Type:"} /></strong> {validatedContent.type}
                        <br />
                        <strong>ID:</strong> {validatedContent.id}
                        <br />
                        <strong><LocalizedText source={"Audio:"} /></strong>{' '}
                        {validatedContent.isAudio ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />} |
                        <strong><LocalizedText source={"Video:"} /></strong>{' '}
                        {validatedContent.isVideo ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />} |
                        <strong><LocalizedText source={"Image:"} /></strong>{' '}
                        {validatedContent.isImage ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />}
                      </p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Domain Search */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="search plus" />
                <LocalizedText source={"Domain Search"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Find ContentIDs by domain and optional type"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Group widths="equal">
                  <Form.Field>
                    <label><LocalizedText source={"Domain"} /></label>
                    <Input
                      onChange={(e) => setDomain(e.target.value)}
                      placeholder={interfaceText("e.g., audio, video, image")}
                      value={domain}
                     {...interfaceTextProps("e.g., audio, video, image")}/>
                  </Form.Field>
                  <Form.Field>
                    <label><LocalizedText source={"Type (optional)"} /></label>
                    <Input
                      onChange={(e) => setType(e.target.value)}
                      placeholder={interfaceText("e.g., track, movie, photo")}
                      value={type}
                     {...interfaceTextProps("e.g., track, movie, photo")}/>
                  </Form.Field>
                </Form.Group>
                <Button
                  disabled={!domain.trim() || searchingDomain}
                  loading={searchingDomain}
                  onClick={handleDomainSearch}
                  primary
                >
                  <LocalizedText source={"Search Domain"} /></Button>
              </Form>

              {domainResults && (
                <div style={{ marginTop: '1em' }}>
                  {domainResults.error ? (
                    <Message error>
                      <p>{domainResults.error}</p>
                    </Message>
                  ) : (
                    <div>
                      <p>
                        <strong>
                          <LocalizedText source={"Found"} />{" "}{domainResults.contentIds?.length || 0}{' '}
                          <LocalizedText source={"ContentIDs"} /></strong>
                      </p>
                      {domainResults.contentIds?.length > 0 && (
                        <List
                          divided
                          relaxed
                          style={{ maxHeight: '200px', overflow: 'auto' }}
                        >
                          {domainResults.contentIds.map((id, index) => (
                            <List.Item key={index}>
                              <List.Content>
                                <code>{id}</code>
                              </List.Content>
                            </List.Item>
                          ))}
                        </List>
                      )}
                    </div>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

        {/* Examples */}
        <Grid.Column width={16}>
          <Segment>
            <Header as="h3">
              <Icon name="lightbulb" />
              <LocalizedText source={"ContentID Examples"} /></Header>
            <p>
              <LocalizedText source={"Click any example to fill the read-only resolve and validation fields, plus the advanced registration fields."} /></p>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5em' }}>
              {Object.entries(contentExamples).map(([domainName, types]) =>
                Object.entries(types).map(([typeName, example]) => (
                  <Button
                    key={`${domainName}-${typeName}`}
                    onClick={() => fillExample(domainName, typeName)}
                    size="small"
                  >
                    {domainName}:{typeName}
                  </Button>
                )),
              )}
            </div>
          </Segment>
        </Grid.Column>

    </>
  );
};

export default React.memo(MediaCoreContentRegistryPanel);
