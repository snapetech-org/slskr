import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import * as mediacore from '../../../lib/mediacore';
import { toDisplayError } from '../../../lib/errors';
import Button from './MediaCoreButton';
import React, { useEffect, useRef } from 'react';
import { formatRegionalFixedNumber, useRegionalFormat } from '../../../lib/util';
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

const MediaCoreTextSimilarityPanel = React.memo(() => {
  useInterfaceLanguage();
  useRegionalFormat();
  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const [textSimilarityA, setTextSimilarityA] = useMountedState(mountedRef, '');
  const [textSimilarityB, setTextSimilarityB] = useMountedState(mountedRef, '');
  const [textSimilarityResult, setTextSimilarityResult] = useMountedState(mountedRef, null);
  const [computingTextSimilarity, setComputingTextSimilarity] = useMountedState(mountedRef, false);

  const handleComputeTextSimilarity = async () => {
    if (!textSimilarityA.trim() || !textSimilarityB.trim()) return;

    try {
      setComputingTextSimilarity(true);
      setTextSimilarityResult(null);
      const result = await mediacore.computeTextSimilarity(
        textSimilarityA.trim(),
        textSimilarityB.trim(),
      );
      setTextSimilarityResult(result);
    } catch (error_) {
      setTextSimilarityResult({ error: toDisplayError(error_) });
    } finally {
      setComputingTextSimilarity(false);
    }
  };

  return (
    <>
        {/* Text Similarity */}
        <Grid.Column width={16}>
          <Card fluid>
            <Card.Content>
              <Card.Header>
                <Icon name="font" />
                <LocalizedText source={"Text Similarity Analysis"} /></Card.Header>
              <Card.Description>
                <LocalizedText source={"Compare text strings using Levenshtein distance and phonetic matching"} /></Card.Description>
            </Card.Content>
            <Card.Content>
              <Form>
                <Form.Group widths="equal">
                  <Form.Field>
                    <label><LocalizedText source={"Text A"} /></label>
                    <Input
                      onChange={(e) => setTextSimilarityA(e.target.value)}
                      placeholder={interfaceText("First text string")}
                      value={textSimilarityA}
                     {...interfaceTextProps("First text string")}/>
                  </Form.Field>
                  <Form.Field>
                    <label><LocalizedText source={"Text B"} /></label>
                    <Input
                      onChange={(e) => setTextSimilarityB(e.target.value)}
                      placeholder={interfaceText("Second text string")}
                      value={textSimilarityB}
                     {...interfaceTextProps("Second text string")}/>
                  </Form.Field>
                </Form.Group>
                <Button
                  disabled={
                    !textSimilarityA.trim() ||
                    !textSimilarityB.trim() ||
                    computingTextSimilarity
                  }
                  loading={computingTextSimilarity}
                  onClick={handleComputeTextSimilarity}
                  primary
                >
                  <LocalizedText source={"Analyze Text Similarity"} /></Button>
              </Form>

              {textSimilarityResult && (
                <div style={{ marginTop: '1em' }}>
                  {textSimilarityResult.error ? (
                    <Message error>
                      <p>{textSimilarityResult.error}</p>
                    </Message>
                  ) : (
                    <Message success>
                      <Message.Header><LocalizedText source={"Text Similarity Results"} /></Message.Header>
                      <p>
                        <strong><LocalizedText source={"Text A:"} /></strong> "{textSimilarityResult.textA}"
                        <br />
                        <strong><LocalizedText source={"Text B:"} /></strong> "{textSimilarityResult.textB}"
                        <br />
                        <strong><LocalizedText source={"Levenshtein Similarity:"} /></strong>{' '}
                        {formatRegionalFixedNumber((
                          textSimilarityResult.levenshteinSimilarity * 100
                        ), 1)}
                        %<br />
                        <strong><LocalizedText source={"Phonetic Similarity:"} /></strong>{' '}
                        {formatRegionalFixedNumber((
                          textSimilarityResult.phoneticSimilarity * 100
                        ), 1)}
                        %<br />
                        <strong><LocalizedText source={"Combined Similarity:"} /></strong>{' '}
                        {formatRegionalFixedNumber((
                          textSimilarityResult.combinedSimilarity * 100
                        ), 1)}
                        %
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

export default MediaCoreTextSimilarityPanel;
