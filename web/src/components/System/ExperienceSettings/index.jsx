import LocalizedText from "../../Shared/LocalizedText";
import { interfaceText, interfaceTextProps, INTERFACE_LANGUAGE_OPTIONS, resetInterfaceLanguage, useInterfaceLanguage } from "../../../lib/interfaceLocale";
import { REGIONAL_FORMAT_OPTIONS } from '../../../lib/regionalFormat';

import {
  EXPERIENCE_PREFERENCES_STORAGE_KEY,
  setRegionalFormatPreference,
  useRegionalFormat,
} from '../../../lib/util';
import { copyToClipboard } from '../../../lib/clipboard';
import { toDisplayError } from '../../../lib/errors';
import { readBoundedJson } from '../../../lib/persistedJson';
import {
  getLocalStorageItem,
  removeLocalStorageItem,
  setLocalStorageItem,
} from '../../../lib/storage';
import { useMountedRef } from '../../../lib/useMountedRef';
import React, { useEffect, useState } from 'react';
import {
  Button,
  Card,
  Checkbox,
  Form,
  Header,
  Icon,
  Message,
  Popup,
  Segment,
} from 'semantic-ui-react';

const localizedOptionLabel = (option, locale = option.value) => {
  const [nativeName, englishName] = option.text.split(' — ');
  const direction = locale === 'ar' ? 'rtl' : 'ltr';

  return (
    <>
      <span dir={direction} lang={locale}>{nativeName}</span>
      {englishName && (
        <>
          {' — '}
          <span dir="ltr" lang="en">{englishName}</span>
        </>
      )}
    </>
  );
};

const interfaceLanguageOptions = INTERFACE_LANGUAGE_OPTIONS.map((option) => ({
  ...option,
  text: localizedOptionLabel(option),
}));
const regionalFormatOptions = REGIONAL_FORMAT_OPTIONS.map((option) => ({
  ...option,
  text: localizedOptionLabel(
    option,
    option.value === 'system' ? 'en' : option.value,
  ),
}));

const storageKey = EXPERIENCE_PREFERENCES_STORAGE_KEY;

const defaults = {
  regionalFormat: 'system',
  discoveryApprovalFilter: 'all',
  discoveryConfidenceFloor: '0.70',
  discoveryExplanationDetail: 'full',
  discoveryProviderFilter: '',
  discoveryStaleDays: '14',
  messagesDenseMode: false,
  messagesPinnedRestore: true,
  messagesRoomUserFilter: true,
  messagesSearchEnabled: true,
  messagesUnreadBadges: true,
  playerCaptureHistory: true,
  playerDefaultVisualizer: 'last',
  playerKeyboardShortcuts: true,
  playerQueueAutoFill: false,
  playerRadioSeedMode: 'current',
  playerScrobbleMode: 'manual',
  playerShowRatings: true,
  searchActionPreviewDensity: 'detailed',
  searchDuplicateFolding: true,
  searchPreferredCondition: 'lossless',
  searchRankingProfile: 'balanced',
};

const options = {
  regionalFormat: regionalFormatOptions,
  actionPreviewDensity: [
    { key: 'compact', get text() { return interfaceText("Compact"); }, value: 'compact' },
    { key: 'detailed', get text() { return interfaceText("Detailed"); }, value: 'detailed' },
  ],
  approvalFilter: [
    { key: 'all', get text() { return interfaceText("All"); }, value: 'all' },
    { key: 'needs-review', get text() { return interfaceText("Needs review"); }, value: 'needs-review' },
    { key: 'approved', get text() { return interfaceText("Approved"); }, value: 'approved' },
    { key: 'snoozed', get text() { return interfaceText("Snoozed"); }, value: 'snoozed' },
  ],
  explanationDetail: [
    { key: 'compact', get text() { return interfaceText("Compact"); }, value: 'compact' },
    { key: 'full', get text() { return interfaceText("Full evidence"); }, value: 'full' },
  ],
  preferredCondition: [
    { key: 'lossless', get text() { return interfaceText("Lossless first"); }, value: 'lossless' },
    { key: 'complete', get text() { return interfaceText("Complete releases first"); }, value: 'complete' },
    { key: 'fastest', get text() { return interfaceText("Fastest source first"); }, value: 'fastest' },
  ],
  radioSeedMode: [
    { key: 'current', get text() { return interfaceText("Current track"); }, value: 'current' },
    { key: 'queue', get text() { return interfaceText("Queue context"); }, value: 'queue' },
    { key: 'history', get text() { return interfaceText("Listening history"); }, value: 'history' },
  ],
  rankingProfile: [
    { key: 'balanced', get text() { return interfaceText("Balanced"); }, value: 'balanced' },
    { key: 'quality', get text() { return interfaceText("Quality"); }, value: 'quality' },
    { key: 'availability', get text() { return interfaceText("Availability"); }, value: 'availability' },
    { key: 'network-light', text: 'Network-light', value: 'network-light' },
  ],
  scrobbleMode: [
    { key: 'manual', get text() { return interfaceText("Manual"); }, value: 'manual' },
    { key: 'review', get text() { return interfaceText("Review before send"); }, value: 'review' },
    { key: 'off', get text() { return interfaceText("Off"); }, value: 'off' },
  ],
  visualizerDefault: [
    { key: 'last', get text() { return interfaceText("Last used"); }, value: 'last' },
    { key: 'art', get text() { return interfaceText("Album art"); }, value: 'art' },
    { key: 'rustymilk-webgl2', get text() { return interfaceText("RustyMilk WebGL2"); }, value: 'rustymilk-webgl2' },
    { key: 'rustymilk-webgpu', get text() { return interfaceText("RustyMilk WebGPU"); }, value: 'rustymilk-webgpu' },
  ],
};

const maxPreferenceTextCharacters = 2_048;
const preferenceOptionValues = {
  regionalFormat: options.regionalFormat.map((option) => option.value),
  discoveryApprovalFilter: options.approvalFilter.map((option) => option.value),
  discoveryExplanationDetail: options.explanationDetail.map((option) => option.value),
  playerDefaultVisualizer: options.visualizerDefault.map((option) => option.value),
  playerRadioSeedMode: options.radioSeedMode.map((option) => option.value),
  playerScrobbleMode: options.scrobbleMode.map((option) => option.value),
  searchActionPreviewDensity: options.actionPreviewDensity.map((option) => option.value),
  searchPreferredCondition: options.preferredCondition.map((option) => option.value),
  searchRankingProfile: options.rankingProfile.map((option) => option.value),
};

const normalizePreferences = (stored = {}) => {
  const source = stored && typeof stored === 'object' && !Array.isArray(stored)
    ? stored
    : {};

  return Object.keys(defaults).reduce((preferences, key) => {
    const defaultValue = defaults[key];
    const value = source[key];

    if (typeof defaultValue === 'boolean') {
      preferences[key] = typeof value === 'boolean' ? value : defaultValue;
      return preferences;
    }

    if (typeof value !== 'string') {
      preferences[key] = defaultValue;
      return preferences;
    }

    const normalized = value.trim().slice(0, maxPreferenceTextCharacters);
    const allowedValues = preferenceOptionValues[key];
    preferences[key] = allowedValues && !allowedValues.includes(normalized)
      ? defaultValue
      : normalized;
    return preferences;
  }, {});
};

const readStoredPreferences = () => {
  const stored = readBoundedJson(
    getLocalStorageItem,
    storageKey,
    {},
    64 * 1024,
  );
  return normalizePreferences(stored);
};

const buildReport = (form) =>
  [
    'slskr experience preferences',
    'Regional format: ' + form.regionalFormat,
    `Search: ranking=${form.searchRankingProfile}, condition=${form.searchPreferredCondition}, duplicate_folding=${form.searchDuplicateFolding}, previews=${form.searchActionPreviewDensity}`,
    `Discovery: provider=${form.discoveryProviderFilter || 'all'}, approval=${form.discoveryApprovalFilter}, confidence>=${form.discoveryConfidenceFloor}, stale_days=${form.discoveryStaleDays}, explanations=${form.discoveryExplanationDetail}`,
    `Player: queue_auto_fill=${form.playerQueueAutoFill}, radio_seed=${form.playerRadioSeedMode}, ratings=${form.playerShowRatings}, history=${form.playerCaptureHistory}, scrobble=${form.playerScrobbleMode}, visualizer=${form.playerDefaultVisualizer}, shortcuts=${form.playerKeyboardShortcuts}`,
    `Messages: dense=${form.messagesDenseMode}, pinned_restore=${form.messagesPinnedRestore}, unread_badges=${form.messagesUnreadBadges}, user_filter=${form.messagesRoomUserFilter}, search=${form.messagesSearchEnabled}`,
  ].join('\n');

const ExperienceSettings = () => {
  const [form, setForm] = useState(defaults);
  const [message, setMessage] = useState(null);
  const mountedRef = useMountedRef();
  const regionalFormat = useRegionalFormat();
  const { language, setLanguage, t } = useInterfaceLanguage();

  useEffect(() => {
    setForm(readStoredPreferences());
  }, []);

  useEffect(() => {
    setForm((current) => ({ ...current, regionalFormat }));
  }, [regionalFormat]);

  const update = (key, value) => {
    setForm((current) => ({ ...current, [key]: value }));
    setMessage(null);
  };

  const save = () => {
    const saved = setLocalStorageItem(
      storageKey,
      JSON.stringify(normalizePreferences(form)),
    );
    setRegionalFormatPreference(form.regionalFormat);
    setMessage(
      saved
        ? 'Experience preferences saved locally in this browser.'
        : 'Unable to save experience preferences in this browser.',
    );
  };

  const reset = () => {
    const preferencesRemoved = removeLocalStorageItem(storageKey);
    const languageRemoved = resetInterfaceLanguage();
    setForm(defaults);
    setRegionalFormatPreference(defaults.regionalFormat);
    setMessage(
      preferencesRemoved && languageRemoved
        ? 'Experience preferences reset to defaults.'
        : 'Unable to reset experience preferences in this browser.',
    );
  };

  const copyReport = async () => {
    const report = buildReport(form);
    try {
      const copied = await copyToClipboard(report);
      if (!mountedRef.current) return;
      setMessage(
        copied
          ? 'Experience preference report copied.'
          : 'Experience preference report prepared; clipboard is unavailable.',
      );
    } catch (error) {
      if (mountedRef.current) {
        setMessage(toDisplayError(error, 'Unable to copy experience preference report.'));
      }
    }
  };

  return (
    <div className="experience-settings" lang="en">
      <Segment>
        <Header as="h3">
          <Icon name="compass" />
          <LocalizedText source={"Experience Preferences"} /></Header>
        <p>
          <LocalizedText source={"Browser-local preference surface for Search, Player, and Messages behavior that can be consumed by page-specific backfill."} /></p>
      </Segment>

      {message && (
        <Message
          positive
          size="small"
        >
          {message}
        </Message>
      )}

      <Card.Group
        itemsPerRow={1}
        stackable
      >
        <Card fluid>
          <Card.Content>
            <Card.Header><Icon name="language" /> <span dir={language === 'ar' ? 'rtl' : 'ltr'} lang={language}>{t('Interface language')}</span></Card.Header>
            <Card.Meta dir={language === 'ar' ? 'rtl' : 'ltr'} lang={language}>{t('Choose the language used for the interface.')} {t('Translations cover navigation, preferences, and transfer labels; other screens use English.')}</Card.Meta>
          </Card.Content>
          <Card.Content>
            <Form>
              <Form.Select
                aria-label={t('Interface language')}
                dir={language === 'ar' ? 'rtl' : 'ltr'}
                label={<span lang={language}>{t('Interface language')}</span>}
                lang={language}
                onChange={(_, { value }) => setLanguage(value)}
                options={interfaceLanguageOptions}
                value={language}
              />
            </Form>
          </Card.Content>
        </Card>
        <Card fluid>
          <Card.Content>
            <Card.Header>
              <Icon name="globe" />
              <span dir={language === 'ar' ? 'rtl' : 'ltr'} lang={language}>{t('Regional format')}</span>
            </Card.Header>
            <Card.Meta dir={language === 'ar' ? 'rtl' : 'ltr'} lang={language}>{t('Choose how dates, times, and numbers are displayed. This setting is separate from interface language.')}</Card.Meta>
          </Card.Content>
          <Card.Content>
            <Form>
              <Form.Select
                aria-label={t('Regional format')}
                dir={language === 'ar' ? 'rtl' : 'ltr'}
                label={<span lang={language}>{t('Date, time, and number format')}</span>}
                lang={language}
                onChange={(_, { value }) => update('regionalFormat', value)}
                options={options.regionalFormat}
                value={form.regionalFormat}
              />
            </Form>
          </Card.Content>
        </Card>
        <Card fluid>
          <Card.Content>
            <Card.Header>
              <Icon name="search" />
              <LocalizedText source={"Search"} /></Card.Header>
            <Card.Meta><LocalizedText source={"Ranking, duplicate folding, preferred conditions, and planned-action density."} /></Card.Meta>
          </Card.Content>
          <Card.Content>
            <Form>
              <Form.Group widths="equal">
                <Form.Select
                  aria-label={interfaceText("Search ranking profile preference")}
                  label={interfaceText("Ranking Profile")}
                  onChange={(_, { value }) => update('searchRankingProfile', value)}
                  options={options.rankingProfile}
                  value={form.searchRankingProfile}
                 {...interfaceTextProps("Search ranking profile preference")}/>
                <Form.Select
                  aria-label={interfaceText("Search preferred condition preference")}
                  label={interfaceText("Preferred Condition")}
                  onChange={(_, { value }) => update('searchPreferredCondition', value)}
                  options={options.preferredCondition}
                  value={form.searchPreferredCondition}
                 {...interfaceTextProps("Search preferred condition preference")}/>
                <Form.Select
                  aria-label={interfaceText("Search action preview density preference")}
                  label={interfaceText("Action Preview Density")}
                  onChange={(_, { value }) =>
                    update('searchActionPreviewDensity', value)
                  }
                  options={options.actionPreviewDensity}
                  value={form.searchActionPreviewDensity}
                 {...interfaceTextProps("Search action preview density preference")}/>
              </Form.Group>
              <Popup
                content={interfaceText("Fold likely duplicate results into a single review row when page support is available.")}
                trigger={
                  <Checkbox
                    aria-label={interfaceText("Enable search duplicate folding preference")}
                    checked={form.searchDuplicateFolding}
                    label={interfaceText("Fold duplicate results")}
                    onChange={(_, { checked }) =>
                      update('searchDuplicateFolding', Boolean(checked))
                    }
                    toggle
                   {...interfaceTextProps("Enable search duplicate folding preference")}/>
                }
               {...interfaceTextProps("Fold likely duplicate results into a single review row when page support is available.")}/>
            </Form>
          </Card.Content>
        </Card>

        <Card fluid>
          <Card.Content>
            <Card.Header>
              <Icon name="play circle" />
              <LocalizedText source={"Player"} /></Card.Header>
            <Card.Meta><LocalizedText source={"Queue, radio, ratings, history, scrobbling, visualizer, and keyboard behavior."} /></Card.Meta>
          </Card.Content>
          <Card.Content>
            <Form>
              <Form.Group widths="equal">
                <Form.Select
                  aria-label={interfaceText("Player radio seed preference")}
                  label={interfaceText("Radio Seed")}
                  onChange={(_, { value }) => update('playerRadioSeedMode', value)}
                  options={options.radioSeedMode}
                  value={form.playerRadioSeedMode}
                 {...interfaceTextProps("Player radio seed preference")}/>
                <Form.Select
                  aria-label={interfaceText("Player scrobble mode preference")}
                  label={interfaceText("Scrobble Mode")}
                  onChange={(_, { value }) => update('playerScrobbleMode', value)}
                  options={options.scrobbleMode}
                  value={form.playerScrobbleMode}
                 {...interfaceTextProps("Player scrobble mode preference")}/>
                <Form.Select
                  aria-label={interfaceText("Player default visualizer preference")}
                  label={interfaceText("Default Visualizer")}
                  onChange={(_, { value }) => update('playerDefaultVisualizer', value)}
                  options={options.visualizerDefault}
                  value={form.playerDefaultVisualizer}
                 {...interfaceTextProps("Player default visualizer preference")}/>
              </Form.Group>
              <Form.Group grouped>
                <Popup
                  content={interfaceText("Allow player pages to append local similar-track queue candidates when explicit page support is available.")}
                  trigger={
                    <Checkbox
                      aria-label={interfaceText("Enable player queue auto-fill preference")}
                      checked={form.playerQueueAutoFill}
                      label={interfaceText("Enable queue auto-fill")}
                      onChange={(_, { checked }) =>
                        update('playerQueueAutoFill', Boolean(checked))
                      }
                      toggle
                     {...interfaceTextProps("Enable player queue auto-fill preference")}/>
                  }
                 {...interfaceTextProps("Allow player pages to append local similar-track queue candidates when explicit page support is available.")}/>
                <Checkbox
                  aria-label={interfaceText("Show player ratings preference")}
                  checked={form.playerShowRatings}
                  label={interfaceText("Show ratings")}
                  onChange={(_, { checked }) =>
                    update('playerShowRatings', Boolean(checked))
                  }
                 {...interfaceTextProps("Show player ratings preference")}/>
                <Checkbox
                  aria-label={interfaceText("Capture player history preference")}
                  checked={form.playerCaptureHistory}
                  label={interfaceText("Capture local history")}
                  onChange={(_, { checked }) =>
                    update('playerCaptureHistory', Boolean(checked))
                  }
                 {...interfaceTextProps("Capture player history preference")}/>
                <Checkbox
                  aria-label={interfaceText("Enable player keyboard shortcuts preference")}
                  checked={form.playerKeyboardShortcuts}
                  label={interfaceText("Enable keyboard shortcuts")}
                  onChange={(_, { checked }) =>
                    update('playerKeyboardShortcuts', Boolean(checked))
                  }
                 {...interfaceTextProps("Enable player keyboard shortcuts preference")}/>
              </Form.Group>
            </Form>
          </Card.Content>
        </Card>

        <Card fluid>
          <Card.Content>
            <Card.Header>
              <Icon name="comments" />
              <LocalizedText source={"Messages"} /></Card.Header>
            <Card.Meta><LocalizedText source={"Dense display, pinned panels, unread badges, user filtering, and local search preference."} /></Card.Meta>
          </Card.Content>
          <Card.Content>
            <Form>
              <Form.Group grouped>
                <Checkbox
                  aria-label={interfaceText("Enable messages dense mode preference")}
                  checked={form.messagesDenseMode}
                  label={interfaceText("Dense display")}
                  onChange={(_, { checked }) =>
                    update('messagesDenseMode', Boolean(checked))
                  }
                 {...interfaceTextProps("Enable messages dense mode preference")}/>
                <Checkbox
                  aria-label={interfaceText("Restore pinned message panels preference")}
                  checked={form.messagesPinnedRestore}
                  label={interfaceText("Restore pinned panels")}
                  onChange={(_, { checked }) =>
                    update('messagesPinnedRestore', Boolean(checked))
                  }
                 {...interfaceTextProps("Restore pinned message panels preference")}/>
                <Checkbox
                  aria-label={interfaceText("Show unread message badges preference")}
                  checked={form.messagesUnreadBadges}
                  label={interfaceText("Show unread badges")}
                  onChange={(_, { checked }) =>
                    update('messagesUnreadBadges', Boolean(checked))
                  }
                 {...interfaceTextProps("Show unread message badges preference")}/>
                <Checkbox
                  aria-label={interfaceText("Enable room user filtering preference")}
                  checked={form.messagesRoomUserFilter}
                  label={interfaceText("Enable room user filtering")}
                  onChange={(_, { checked }) =>
                    update('messagesRoomUserFilter', Boolean(checked))
                  }
                 {...interfaceTextProps("Enable room user filtering preference")}/>
                <Checkbox
                  aria-label={interfaceText("Enable local message search preference")}
                  checked={form.messagesSearchEnabled}
                  label={interfaceText("Enable local message search")}
                  onChange={(_, { checked }) =>
                    update('messagesSearchEnabled', Boolean(checked))
                  }
                 {...interfaceTextProps("Enable local message search preference")}/>
              </Form.Group>
            </Form>
          </Card.Content>
        </Card>
      </Card.Group>

      <div className="integration-actions">
        <Popup
          content={interfaceText("Save these preference choices to this browser. No server settings, searches, downloads, messages, or files are changed.")}
          trigger={
            <Button
              icon
              labelPosition="left"
              onClick={save}
              primary
            >
              <Icon name="save" />
              <LocalizedText source={"Save Local Preferences"} /></Button>
          }
         {...interfaceTextProps("Save these preference choices to this browser. No server settings, searches, downloads, messages, or files are changed.")}/>
        <Popup
          content={interfaceText("Reset these browser-local preference choices to the slskr defaults.")}
          trigger={
            <Button
              icon
              labelPosition="left"
              onClick={reset}
            >
              <Icon name="undo" />
              <LocalizedText source={"Reset"} /></Button>
          }
         {...interfaceTextProps("Reset these browser-local preference choices to the slskr defaults.")}/>
        <Popup
          content={interfaceText("Copy a review report of the selected preferences for implementation handoff.")}
          trigger={
            <Button
              icon
              labelPosition="left"
              onClick={copyReport}
            >
              <Icon name="copy" />
              <LocalizedText source={"Copy Report"} /></Button>
          }
         {...interfaceTextProps("Copy a review report of the selected preferences for implementation handoff.")}/>
      </div>
    </div>
  );
};

export default ExperienceSettings;
