import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import React, { useEffect, useRef } from 'react';
import { Card, Form, Grid, Icon, Input, Message } from 'semantic-ui-react';

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

const MediaCoreHashSimilarityPanel = React.memo(() => {
  useInterfaceLanguage();
  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const [hashA, setHashA] = useMountedState(mountedRef, '');
  const [hashB, setHashB] = useMountedState(mountedRef, '');
  const [similarityThreshold, setSimilarityThreshold] = useMountedState(mountedRef, 0.8);
  const [similarityResult, setSimilarityResult] = useMountedState(mountedRef, null);
  const [computingSimilarity, setComputingSimilarity] = useMountedState(mountedRef, false);

  const handleComputeSimilarity = async () => {
    if (!hashA.trim() || !hashB.trim()) return;

    try {
      setComputingSimilarity(true);
      setSimilarityResult(null);
      const result = await mediacore.computeHashSimilarity(
        hashA.trim(),
        hashB.trim(),
        Number.parseFloat(similarityThreshold),
      );
      setSimilarityResult(result);
    } catch (error_) {
      setSimilarityResult({ error: toDisplayError(error_) });
    } finally {
      setComputingSimilarity(false);
    }
  };

  return (
    <>
        {/* Hash Similarity Analysis */}
        <Grid.Column width={16}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="balance scale" />
                <LocalizedText source={"Hash Similarity Analysis"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Compare perceptual hashes to determine content similarity"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Group widths="equal">
                  <Form.Field>
                    <label><LocalizedText source={"Hash A (hex)"} /></label>
                    <Input
                      onChange={(e) => setHashA(e.target.value)}
                      placeholder={interfaceText("First hash value (hexadecimal)")}
                      value={hashA}
                     {...interfaceTextProps("First hash value (hexadecimal)")}/>
                  </Form.Field>
                  <Form.Field>
                    <label><LocalizedText source={"Hash B (hex)"} /></label>
                    <Input
                      onChange={(e) => setHashB(e.target.value)}
                      placeholder={interfaceText("Second hash value (hexadecimal)")}
                      value={hashB}
                     {...interfaceTextProps("Second hash value (hexadecimal)")}/>
                  </Form.Field>
                  <Form.Field>
                    <label><LocalizedText source={"Similarity Threshold"} /></label>
                    <Input
                      max="1"
                      min="0"
                      onChange={(e) => setSimilarityThreshold(e.target.value)}
                      step="0.1"
                      type="number"
                      value={similarityThreshold}
                    />
                  </Form.Field>
                </Form.Group>
                <Button
                  disabled={
                    !hashA.trim() || !hashB.trim() || computingSimilarity
                  }
                  loading={computingSimilarity}
                  onClick={handleComputeSimilarity}
                  primary
                >
                  <LocalizedText source={"Analyze Similarity"} /></Button>
              </Form>

              {similarityResult && (
                <div style={{ marginTop: '1em' }}>
                  {similarityResult.error ? (
                    <Message error>
                      <p>{similarityResult.error}</p>
                    </Message>
                  ) : (
                    <Message info>
                      <Message.Header>
                        <LocalizedText source={"Similarity Analysis Results"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Hamming Distance:"} /></strong>{' '}
                        {similarityResult.hammingDistance} <LocalizedText source={"bits"} /><br />
                        <strong><LocalizedText source={"Similarity Score:"} /></strong>{' '}
                        {(similarityResult.similarity * 100).toFixed(1)}%<br />
                        <strong><LocalizedText source={"Are Similar:"} /></strong>{' '}
                        {similarityResult.areSimilar ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />} <LocalizedText source={"(threshold:"} />{' '}
                        {(similarityResult.threshold * 100).toFixed(1)}%)
                      </p>
                    </Message>
                  )}
                </div>
              )}
            </Card.Content>
          </Card>
        </Grid.Column>

    </>
  );
});

export default MediaCoreHashSimilarityPanel;
