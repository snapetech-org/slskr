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

const MediaCorePerceptualSimilarityPanel = React.memo(() => {
  useInterfaceLanguage();
  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const [perceptualContentIdA, setPerceptualContentIdA] = useMountedState(mountedRef, '');
  const [perceptualContentIdB, setPerceptualContentIdB] = useMountedState(mountedRef, '');
  const [perceptualThreshold, setPerceptualThreshold] = useMountedState(mountedRef, 0.7);
  const [perceptualSimilarityResult, setPerceptualSimilarityResult] =
    useMountedState(mountedRef, null);
  const [computingPerceptualSimilarity, setComputingPerceptualSimilarity] =
    useMountedState(mountedRef, false);

  const handleComputePerceptualSimilarity = async () => {
    if (!perceptualContentIdA.trim() || !perceptualContentIdB.trim()) return;

    try {
      setComputingPerceptualSimilarity(true);
      setPerceptualSimilarityResult(null);
      const result = await mediacore.computePerceptualSimilarity(
        perceptualContentIdA.trim(),
        perceptualContentIdB.trim(),
        Number.parseFloat(perceptualThreshold),
      );
      setPerceptualSimilarityResult(result);
    } catch (error_) {
      setPerceptualSimilarityResult({ error: toDisplayError(error_) });
    } finally {
      setComputingPerceptualSimilarity(false);
    }
  };

  return (
    <>
        {/* Perceptual Similarity */}
        <Grid.Column width={8}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="chart bar" />
                <LocalizedText source={"Perceptual Similarity"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Compare perceptual similarity between two ContentIDs"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Group widths="equal">
                  <Form.Field>
                    <label><LocalizedText source={"ContentID A"} /></label>
                    <Input
                      onChange={(e) => setPerceptualContentIdA(e.target.value)}
                      placeholder={interfaceText("First ContentID")}
                      value={perceptualContentIdA}
                     {...interfaceTextProps("First ContentID")}/>
                  </Form.Field>
                  <Form.Field>
                    <label><LocalizedText source={"ContentID B"} /></label>
                    <Input
                      onChange={(e) => setPerceptualContentIdB(e.target.value)}
                      placeholder={interfaceText("Second ContentID")}
                      value={perceptualContentIdB}
                     {...interfaceTextProps("Second ContentID")}/>
                  </Form.Field>
                </Form.Group>
                <Form.Field>
                  <label><LocalizedText source={"Similarity Threshold"} /></label>
                  <Input
                    max="1"
                    min="0"
                    onChange={(e) => setPerceptualThreshold(e.target.value)}
                    step="0.1"
                    type="number"
                    value={perceptualThreshold}
                  />
                </Form.Field>
                <Button
                  disabled={
                    !perceptualContentIdA.trim() ||
                    !perceptualContentIdB.trim() ||
                    computingPerceptualSimilarity
                  }
                  loading={computingPerceptualSimilarity}
                  onClick={handleComputePerceptualSimilarity}
                  primary
                >
                  <LocalizedText source={"Compute Similarity"} /></Button>
              </Form>

              {perceptualSimilarityResult && (
                <div style={{ marginTop: '1em' }}>
                  {perceptualSimilarityResult.error ? (
                    <Message error>
                      <p>{perceptualSimilarityResult.error}</p>
                    </Message>
                  ) : (
                    <Message info>
                      <Message.Header><LocalizedText source={"Similarity Analysis"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Content A:"} /></strong>{' '}
                        {perceptualSimilarityResult.contentIdA}
                        <br />
                        <strong><LocalizedText source={"Content B:"} /></strong>{' '}
                        {perceptualSimilarityResult.contentIdB}
                        <br />
                        <strong><LocalizedText source={"Similarity:"} /></strong>{' '}
                        {(perceptualSimilarityResult.similarity * 100).toFixed(
                          1,
                        )}
                        %<br />
                        <strong><LocalizedText source={"Are Similar:"} /></strong>{' '}
                        {perceptualSimilarityResult.isSimilar ? <LocalizedText source={"Yes"} /> : <LocalizedText source={"No"} />}{' '}
                        <LocalizedText source={"(threshold:"} />{' '}
                        {(perceptualSimilarityResult.threshold * 100).toFixed(
                          1,
                        )}
                        %)
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

export default MediaCorePerceptualSimilarityPanel;
