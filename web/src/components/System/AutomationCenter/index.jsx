import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import { formatRegionalDateTime, formatRegionalNumber, useRegionalFormat } from '../../../lib/util';
import {
  automationRecipes,
  buildAutomationExecutionReport,
  buildAutomationRunHistory,
  formatAutomationRunHistoryReport,
  getAutomationRecipeInputs,
  getAutomationRecipeState,
  isAutomationRecipeExecutable,
  setAutomationRecipeInput,
  setAutomationRecipeDryRun,
  setAutomationRecipeEnabled,
  setAutomationRecipeExecution,
} from '../../../lib/automationRecipes';
import { getRunnableWishlistRequests } from '../../../lib/acquisitionRequests';
import { executeAutomationAction } from '../../../lib/automationActions';
import { toDisplayError } from '../../../lib/errors';
import * as libraryHealthAPI from '../../../lib/libraryHealth';
import * as wishlistAPI from '../../../lib/wishlist';
import { useMountedRef } from '../../../lib/useMountedRef';
import React, { useMemo, useRef, useState } from 'react';
import { toast } from 'react-toastify';
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
  Statistic,
} from 'semantic-ui-react';

const impactColor = (impact) => {
  if (/public/i.test(impact)) {
    return 'orange';
  }

  if (/trusted|metadata|configured|local network/i.test(impact)) {
    return 'blue';
  }

  return 'green';
};

const formatLastDryRun = (value) => {
  if (!value) {
    return 'Not run yet';
  }

  return formatRegionalDateTime(value);
};

const AutomationCenter = () => {
  useRegionalFormat();
  useInterfaceLanguage();
  const [recipeState, setRecipeState] = useState(getAutomationRecipeState);
  const [recipeInputs, setRecipeInputs] = useState(getAutomationRecipeInputs);
  const [copyStatus, setCopyStatus] = useState('');
  const [executingRecipe, setExecutingRecipe] = useState('');
  const mountedRef = useMountedRef();
  const executionRequestIdRef = useRef(0);
  const executionInFlightRef = useRef(false);
  const summary = useMemo(() => {
    const enabled = automationRecipes.filter(
      (recipe) => recipeState[recipe.id]?.enabled,
    ).length;

    return {
      disabled: automationRecipes.length - enabled,
      enabled,
      total: automationRecipes.length,
    };
  }, [recipeState]);
  const runHistory = useMemo(
    () => buildAutomationRunHistory(recipeState),
    [recipeState],
  );

  const toggleRecipe = (recipe, enabled) => {
    setRecipeState(setAutomationRecipeEnabled(recipe.id, enabled));
    toast.info(interfaceText(enabled ? "{title} enabled" : "{title} disabled", { title: interfaceText(recipe.title) }));
  };

  const dryRunRecipe = (recipe) => {
    setRecipeState(setAutomationRecipeDryRun(recipe.id));
    toast.info(interfaceText("{title} dry run recorded", { title: interfaceText(recipe.title) }));
  };

  const executeWishlistRetry = async (recipe, isCurrentRequest) => {
    const response = await wishlistAPI.getAll();
    if (!isCurrentRequest()) return;
    const allRequests = Array.isArray(response)
      ? response.filter(
          (request) =>
            request &&
            typeof request === 'object' &&
            !Array.isArray(request),
        )
      : [];
    const runnableRequests = getRunnableWishlistRequests(allRequests, { limit: 3 });
    const result = {
      failed: 0,
      runLimit: 3,
      skipped: Math.max(allRequests.length - runnableRequests.length, 0),
      started: 0,
    };

    for (const request of runnableRequests) {
      try {
        await wishlistAPI.runSearch(request.id);
        if (!isCurrentRequest()) return;
        result.started += 1;
      } catch {
        result.failed += 1;
      }
    }

    if (!isCurrentRequest()) return;
    result.summary = `Ran ${formatRegionalNumber(result.started)} Wishlist searches; ${formatRegionalNumber(result.failed)} failed; ${formatRegionalNumber(result.skipped)} skipped.`;
    const report = buildAutomationExecutionReport(recipe, result);
    setRecipeState(setAutomationRecipeExecution(recipe.id, report, report.generatedAt));
    const status = interfaceText("{title} ran {started} bounded Wishlist searches; {failed} failed. Downloads still require normal result review.", { title: interfaceText(recipe.title), started: result.started, failed: result.failed });
    setCopyStatus(status);
    toast.info(status);
  };

  const executeLibraryHealthScan = async (recipe, isCurrentRequest) => {
    const libraryPath = `${recipeInputs[recipe.id]?.libraryPath || ''}`.trim();
    if (!libraryPath) {
      setCopyStatus(interfaceText('Enter a Library Health path before starting the scan.'));
      return;
    }

    const response = await libraryHealthAPI.startScan(libraryPath);
    if (!isCurrentRequest()) return;
    const rawScanId = response?.data?.scanId || response?.scanId;
    const scanId =
      typeof rawScanId === 'string' || typeof rawScanId === 'number'
        ? String(rawScanId)
        : 'unknown';
    const report = buildAutomationExecutionReport(recipe, {
      scanId,
      started: 1,
      summary: `Started Library Health scan ${scanId} for ${libraryPath}.`,
    });
    setRecipeState(setAutomationRecipeExecution(recipe.id, report, report.generatedAt));
    const status = interfaceText("{title} started scan {scanId} for {libraryPath}.", { title: interfaceText(recipe.title), scanId, libraryPath });
    setCopyStatus(status);
    toast.info(status);
  };

  const executeReadOnlyRecipe = async (recipe, isCurrentRequest) => {
    const result = await executeAutomationAction(recipe.id);
    if (!isCurrentRequest()) return;
    const report = buildAutomationExecutionReport(recipe, result);
    setRecipeState(setAutomationRecipeExecution(recipe.id, report, report.generatedAt));
    const summary =
      typeof result?.summary === 'string'
        ? result.summary
        : toDisplayError(result, `${recipe.title} completed`);
    setCopyStatus(interfaceText("{title}: {summary}", { title: interfaceText(recipe.title), summary }));
    toast.info(interfaceText("{title} completed", { title: interfaceText(recipe.title) }));
  };

  const executeRecipe = async (recipe) => {
    if (!mountedRef.current || executionInFlightRef.current) return;
    const requestId = ++executionRequestIdRef.current;
    const isCurrentRequest = () =>
      mountedRef.current && executionRequestIdRef.current === requestId;

    if (!isAutomationRecipeExecutable(recipe)) {
      if (isCurrentRequest()) {
        setCopyStatus(interfaceText("{title} is preview-only because its backend action is unavailable.", { title: interfaceText(recipe.title) }));
      }
      return;
    }

    executionInFlightRef.current = true;
    setExecutingRecipe(recipe.id);
    try {
      if (recipe.id === 'wishlist-retry') {
        await executeWishlistRetry(recipe, isCurrentRequest);
      }
      if (recipe.id === 'library-health-scan') {
        await executeLibraryHealthScan(recipe, isCurrentRequest);
      }
      if (['dashboard-refresh', 'local-diagnostics', 'stale-cache-reminders'].includes(recipe.id)) {
        await executeReadOnlyRecipe(recipe, isCurrentRequest);
      }
    } catch (error) {
      if (isCurrentRequest()) {
        const message = interfaceText("{title} failed: {message}", { title: interfaceText(recipe.title), message: toDisplayError(error) });
        setCopyStatus(message);
        toast.error(message);
      }
    } finally {
      executionInFlightRef.current = false;
      if (isCurrentRequest()) setExecutingRecipe('');
    }
  };

  const updateRecipeInput = (recipe, input) => {
    setRecipeInputs(setAutomationRecipeInput(recipe.id, input));
  };

  const copyHistoryReport = async () => {
    if (!mountedRef.current) return;
    const report = formatAutomationRunHistoryReport(runHistory);
    if (!navigator.clipboard?.writeText) {
      setCopyStatus(interfaceText('Clipboard unavailable; copy the automation history manually.'));
      return;
    }

    try {
      await navigator.clipboard.writeText(report);
      if (mountedRef.current) setCopyStatus(interfaceText('Automation history report copied.'));
    } catch {
      if (mountedRef.current) setCopyStatus(interfaceText('Unable to copy automation history report.'));
    }
  };

  return (
    <div className="automation-center">
      <Header as="h3">
        <Icon name="magic" />
        <Header.Content>
          <LocalizedText source={"Automation Center"} /><Header.Subheader>
            <LocalizedText source={"Every automation is visible here. Enable recipes when their impact fits your node; execution is manual and requires the real backend action to be available."} /></Header.Subheader>
        </Header.Content>
      </Header>
      <div className="automation-center-actions">
        <Popup
          content={interfaceText("Copy enabled recipes and dry-run checkpoints for operator review. This does not execute any automation.")}
          position="top center"
          trigger={
            <Button
              aria-label={interfaceText("Copy automation review history")}
              onClick={copyHistoryReport}
              size="small"
             {...interfaceTextProps("Copy automation review history")}>
              <Icon name="copy" />
              <LocalizedText source={"Copy History"} /></Button>
          }
         {...interfaceTextProps("Copy enabled recipes and dry-run checkpoints for operator review. This does not execute any automation.")}/>
      </div>
      {copyStatus && (
        <Message
          info
          size="small"
        >
          {copyStatus}
        </Message>
      )}

      <Statistic.Group
        className="automation-summary"
        size="small"
        widths="three"
      >
        <Statistic>
          <Statistic.Value>{formatRegionalNumber(summary.total)}</Statistic.Value>
          <Statistic.Label><LocalizedText source={"Recipes"} /></Statistic.Label>
        </Statistic>
        <Statistic color="green">
          <Statistic.Value>{formatRegionalNumber(summary.enabled)}</Statistic.Value>
          <Statistic.Label><LocalizedText source={"Enabled"} /></Statistic.Label>
        </Statistic>
        <Statistic color="orange">
          <Statistic.Value>{formatRegionalNumber(summary.disabled)}</Statistic.Value>
          <Statistic.Label><LocalizedText source={"Visible Disabled"} /></Statistic.Label>
        </Statistic>
      </Statistic.Group>

      <div className="automation-history-panel">
        <Header as="h4">
          <Icon name="history" />
          <LocalizedText source={"Review History"} /></Header>
        {runHistory.length === 0 ? (
          <p><LocalizedText source={"No enabled recipes or dry-run checkpoints yet."} /></p>
        ) : (
          <div className="automation-recipe-labels">
            {runHistory.map((entry) => (
              <Label
                basic
                color={entry.lastRunAt ? 'purple' : entry.lastDryRunAt ? 'green' : 'grey'}
                key={entry.recipeId}
              >
                {interfaceText(entry.title)}
                <Label.Detail>
                  {formatLastDryRun(entry.lastRunAt || entry.lastDryRunAt)}
                </Label.Detail>
              </Label>
            ))}
          </div>
        )}
      </div>

      <Card.Group
        className="automation-recipe-grid"
        itemsPerRow={2}
        stackable
      >
        {automationRecipes.map((recipe) => {
          const state = recipeState[recipe.id] ?? {};
          const enabled = state.enabled === true;
          const executable = isAutomationRecipeExecutable(recipe);
          const executing = executingRecipe === recipe.id;
          const libraryHealthPath =
            typeof recipeInputs[recipe.id]?.libraryPath === 'string'
              ? recipeInputs[recipe.id].libraryPath
              : '';
          const missingRequiredInput =
            recipe.id === 'library-health-scan' && !libraryHealthPath.trim();

          return (
            <Card
              className="automation-recipe-card"
              key={recipe.id}
            >
              <Card.Content>
                <div className="automation-recipe-head">
                  <Header
                    as="h4"
                    className="automation-recipe-title"
                  >
                    <Icon name={recipe.icon} />
                    <Header.Content><LocalizedText source={recipe.title} /></Header.Content>
                  </Header>
                  <Popup
                    content={interfaceText(enabled ? "Disable {title}. Disabled recipes remain visible so setup work is discoverable." : "Enable {title}. Disabled recipes remain visible so setup work is discoverable.", { title: interfaceText(recipe.title) })}
                    position="top center"
                    trigger={
                      <Checkbox
                        aria-label={interfaceText(enabled ? "Disable {title}" : "Enable {title}", { title: interfaceText(recipe.title) })}
                        checked={enabled}
                        onChange={(_event, { checked }) =>
                          toggleRecipe(recipe, checked)
                        }
                        toggle
                      />
                    }
                  />
                </div>
                <Card.Description><LocalizedText source={recipe.description} /></Card.Description>
                {recipe.id === 'library-health-scan' && (
                  <Form className="automation-recipe-config">
                    <Form.Input
                      aria-label={interfaceText("Library Health scan path")}
                      fluid
                      icon="folder open outline"
                      onChange={(_event, { value }) =>
                        updateRecipeInput(recipe, { libraryPath: value })
                      }
                      placeholder="/music/library"
                      value={libraryHealthPath}
                     {...interfaceTextProps("Library Health scan path")}/>
                  </Form>
                )}
                <div className="automation-recipe-labels">
                  <Label basic>
                    <Icon name="clock outline" />
                    <LocalizedText source={recipe.cadence} />
                  </Label>
                  <Label basic>
                    <Icon name="hourglass half" />
                    <LocalizedText source={"Cooldown"} />{" "}<LocalizedText source={recipe.cooldown} />
                  </Label>
                  <Label basic>
                    <Icon name="stopwatch" />
                    <LocalizedText source={"Max"} />{" "}<LocalizedText source={recipe.maxRunTime} />
                  </Label>
                  <Label
                    basic
                    color={impactColor(recipe.networkImpact)}
                  >
                    <Icon name="sitemap" />
                    <LocalizedText source={recipe.networkImpact} />
                  </Label>
                  <Label basic>
                    <Icon name="file outline" />
                    <LocalizedText source={recipe.fileImpact} />
                  </Label>
                  <Label basic>
                    <Icon name="lock" />
                    <LocalizedText source={recipe.approvalGate} />
                  </Label>
                </div>
              </Card.Content>
              <Card.Content extra>
                <div className="automation-recipe-actions">
                  <span className="automation-recipe-dry-run">
                    <LocalizedText source={"Dry run:"} />{" "}{formatLastDryRun(state.lastDryRunAt)}
                  </span>
                  {state.lastDryRunReport && (
                    <Label
                      basic
                      color="green"
                    >
                      <LocalizedText source={"Preview only"} /></Label>
                  )}
                  {state.lastRunReport && (
                    <Label
                      basic
                      color="purple"
                    >
                      <LocalizedText source={"Executed"} /></Label>
                  )}
                  <Popup
                    content={interfaceText("Record a dry run checkpoint for {title}. This records the plan without executing the action.", { title: interfaceText(recipe.title) })}
                    position="top center"
                    trigger={
                      <Button
                        aria-label={interfaceText("Record dry run for {title}", { title: interfaceText(recipe.title) })}
                        basic
                        icon
                        onClick={() => dryRunRecipe(recipe)}
                        size="small"
                        title={interfaceText("Record dry run for {title}", { title: interfaceText(recipe.title) })}
                       {...interfaceTextProps("Record dry run for {title}")}>
                        <Icon name="play circle outline" />
                      </Button>
                    }
                   {...interfaceTextProps("Record a dry run checkpoint for {title}. This records the plan without executing the action.")}/>
                  <Popup
                    content={
                      executable
                        ? interfaceText('Execute {title} now through its real backend action. Wishlist Retry runs up to three enabled searches; Library Health starts the configured read-only scan.', {
                          title: interfaceText(recipe.title),
                        })
                        : interfaceText('No live backend action is available for {title}. This recipe remains a policy preview until its backend contract exists.', {
                          title: interfaceText(recipe.title),
                        })
                    }
                    position="top center"
                    trigger={
                      <span>
                        <Button
                          aria-label={interfaceText("Execute {title}", { title: interfaceText(recipe.title) })}
                          disabled={
                            !enabled ||
                            !executable ||
                            Boolean(executingRecipe) ||
                            executing ||
                            missingRequiredInput
                          }
                          icon
                          loading={executing}
                          onClick={() => executeRecipe(recipe)}
                          size="small"
                          title={interfaceText("Execute {title}", { title: interfaceText(recipe.title) })}
                         {...interfaceTextProps("Execute {title}")}>
                          <Icon name="bolt" />
                        </Button>
                      </span>
                    }
                  />
                </div>
              </Card.Content>
            </Card>
          );
        })}
      </Card.Group>
    </div>
  );
};

export default AutomationCenter;
