import { interfaceText, interfaceTextAttributes, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import { LocalizedPopup } from '../Shared/TooltipButton';
import React from 'react';
import { Button, Icon, Popup } from 'semantic-ui-react';
import {
  getEngineIcon,
  getEngineLabel,
  getNextEngine,
  getRustyMilkAutomationLabel,
  isRustyMilkEngine,
  nativeEditableParameters,
} from './visualizerPresetLibrary';

const VisualizerOverlayControls = ({
  actions,
  compactControls,
  mode,
  onModeChange,
  refs,
  state,
}) => {
  useInterfaceLanguage();
  const {
    activeEngineType,
    activeNativePlaylistId,
    activeRustyMilkPresetId,
    activeRustyMilkPresetIsFavorite,
    canSaveNativePlaylist,
    hasNativeShapes,
    hasNativeWaves,
    hasRustyMilkPresetSearch,
    nativeBankNavigationDisabled,
    nativeFpsCap,
    nativeQualityPreset,
    rustyMilkAutomationMode,
    rustyMilkAutomationSettings,
    rustyMilkFavoritePresetIds,
    rustyMilkFragmentSummary,
    rustyMilkLibraryMode,
    rustyMilkParameter,
    rustyMilkParameterValue,
    rustyMilkPresetLibrary,
    rustyMilkPresetPlaylists,
    rustyMilkPresetSearch,
    selectedNativeShapeIndex,
    selectedNativeWaveIndex,
    selectedRustyMilkParameter,
    selectedRustyMilkPresetValue,
    showNativeDebug,
    visibleRustyMilkPresetLibrary,
  } = state;
  const {
    applyRustyMilkParameterEdit,
    clearActiveNativePlaylist,
    clearRustyMilkPresetLibrary,
    clearRustyMilkPresetSearch,
    cycleEngineType,
    cyclePreset,
    cycleRustyMilkAutomationMode,
    enterFullscreen,
    exitFullscreen,
    exportRustyMilkFragment,
    exportRustyMilkPreset,
    importRustyMilkPreset,
    loadRustyMilkLibraryPreset,
    previousRustyMilkLibraryPreset,
    randomRustyMilkLibraryPreset,
    randomizeRustyMilkPresetParameters,
    removeActiveNativePlaylist,
    removeActiveRustyMilkPreset,
    removeRustyMilkFragment,
    renameActiveNativePlaylist,
    saveNativePlaylistFromVisibleBank,
    selectNativePlaylist,
    selectRustyMilkParameter,
    setSelectedNativeShapeIndex,
    setSelectedNativeWaveIndex,
    setShowNativeDebug,
    toggleRustyMilkLibraryMode,
    toggleRustyMilkPresetFavorite,
    updateNativeFpsCap,
    updateNativeQualityPreset,
    updateRustyMilkAutomationBeats,
    updateRustyMilkAutomationInterval,
    updateRustyMilkParameterDraft,
    updateRustyMilkPresetSearch,
  } = actions;
  const { directoryInputRef, fileInputRef } = refs;

  return (
        <div
          className="player-visualizer-overlay-controls"
          onClick={(event) => event.stopPropagation()}
        >
          <input
            accept=".milk,.milk2,.shape,.wave,text/plain,image/png,image/jpeg,image/webp,image/gif"
            hidden
            multiple
            onChange={importRustyMilkPreset}
            ref={fileInputRef}
            type="file"
          />
          <input
            data-testid="visualizer-native-pack-input"
            directory=""
            hidden
            multiple
            onChange={importRustyMilkPreset}
            ref={directoryInputRef}
            type="file"
            webkitdirectory=""
          />
          <LocalizedPopup
            content="Cycle visualizer engine to {engine}."
            parameters={{ engine: getEngineLabel(getNextEngine(activeEngineType)) }}
            trigger={
              <Button
                aria-label={interfaceText('Cycle visualizer engine to {engine}', {
                  engine: getEngineLabel(getNextEngine(activeEngineType)),
                })}
                data-testid="visualizer-switch-engine"
                icon
                onClick={cycleEngineType}
                size="mini"
              >
                <Icon name={getEngineIcon(activeEngineType)} />
              </Button>
            }
          />
          {isRustyMilkEngine(activeEngineType) && !compactControls ? (
            <>
              {rustyMilkPresetLibrary.length > 0 ? (
                <Popup
                  content={interfaceText("Filter imported RustyMilk presets by title or file name. The current filter also scopes next and random preset jumps.")}
                  trigger={
                    <input
                      aria-label={interfaceText("Search RustyMilk presets")}
                      className="player-visualizer-native-search"
                      data-testid="visualizer-native-preset-search"
                      onChange={updateRustyMilkPresetSearch}
                      placeholder={interfaceText("Search presets")}
                      type="search"
                      value={rustyMilkPresetSearch}
                     {...interfaceTextProps("Search RustyMilk presets")}/>
                  }
                 {...interfaceTextProps("Filter imported RustyMilk presets by title or file name. The current filter also scopes next and random preset jumps.")}/>
              ) : null}
              {rustyMilkPresetLibrary.length > 0 ? (
                <Popup
                  content={interfaceText("Clear the RustyMilk preset search filter.")}
                  trigger={
                    <Button
                      aria-label={interfaceText("Clear RustyMilk preset search")}
                      data-testid="visualizer-clear-native-preset-search"
                      disabled={!hasRustyMilkPresetSearch}
                      icon
                      onClick={clearRustyMilkPresetSearch}
                      size="mini"
                     {...interfaceTextProps("Clear RustyMilk preset search")}>
                      <Icon name="remove" />
                    </Button>
                  }
                 {...interfaceTextProps("Clear the RustyMilk preset search filter.")}/>
              ) : null}
              {rustyMilkPresetPlaylists.length > 0 ? (
                <Popup
                  content={interfaceText("Use a saved native playlist as the active preset bank.")}
                  trigger={
                    <select
                      aria-label={interfaceText("RustyMilk playlist")}
                      className="player-visualizer-native-library"
                      data-testid="visualizer-native-playlist"
                      onChange={selectNativePlaylist}
                      value={activeNativePlaylistId}
                     {...interfaceTextProps("RustyMilk playlist")}>
                      <option value="">{interfaceText("All imported")}</option>
                      {rustyMilkPresetPlaylists.map((playlist) => (
                        <option key={playlist.id} value={playlist.id}>
                          {playlist.name}
                        </option>
                      ))}
                    </select>
                  }
                 {...interfaceTextProps("Use a saved native playlist as the active preset bank.")}/>
              ) : null}
              {rustyMilkPresetLibrary.length > 0 ? (
                <Popup
                  content={interfaceText("Save the current visible RustyMilk preset bank as a browser-local playlist.")}
                  trigger={
                    <Button
                      aria-label={interfaceText("Save visible RustyMilk presets as playlist")}
                      data-testid="visualizer-save-native-playlist"
                      disabled={!canSaveNativePlaylist}
                      icon
                      onClick={saveNativePlaylistFromVisibleBank}
                      size="mini"
                     {...interfaceTextProps("Save visible RustyMilk presets as playlist")}>
                      <Icon name="save outline" />
                    </Button>
                  }
                 {...interfaceTextProps("Save the current visible RustyMilk preset bank as a browser-local playlist.")}/>
              ) : null}
              {activeNativePlaylistId ? (
                <Popup
                  content={interfaceText("Rename the active native playlist in this browser.")}
                  trigger={
                    <Button
                      aria-label={interfaceText("Rename active native playlist")}
                      data-testid="visualizer-rename-native-playlist"
                      icon
                      onClick={renameActiveNativePlaylist}
                      size="mini"
                     {...interfaceTextProps("Rename active native playlist")}>
                      <Icon name="edit outline" />
                    </Button>
                  }
                 {...interfaceTextProps("Rename the active native playlist in this browser.")}/>
              ) : null}
              {activeNativePlaylistId ? (
                <Popup
                  content={interfaceText("Return to the full imported RustyMilk preset bank without deleting this playlist.")}
                  trigger={
                    <Button
                      aria-label={interfaceText("Clear active native playlist")}
                      data-testid="visualizer-clear-active-native-playlist"
                      icon
                      onClick={clearActiveNativePlaylist}
                      size="mini"
                     {...interfaceTextProps("Clear active native playlist")}>
                      <Icon name="list" />
                    </Button>
                  }
                 {...interfaceTextProps("Return to the full imported RustyMilk preset bank without deleting this playlist.")}/>
              ) : null}
              {activeNativePlaylistId ? (
                <Popup
                  content={interfaceText("Delete the active native playlist from this browser.")}
                  trigger={
                    <Button
                      aria-label={interfaceText("Delete active native playlist")}
                      data-testid="visualizer-remove-native-playlist"
                      icon
                      onClick={removeActiveNativePlaylist}
                      size="mini"
                     {...interfaceTextProps("Delete active native playlist")}>
                      <Icon name="times circle outline" />
                    </Button>
                  }
                 {...interfaceTextProps("Delete the active native playlist from this browser.")}/>
              ) : null}
              {rustyMilkPresetLibrary.length > 0 ? (
                <LocalizedPopup
                  content={rustyMilkLibraryMode === 'favorites'
                    ? 'Reload a favorite RustyMilk preset from this browser.'
                    : 'Reload a previously imported RustyMilk preset from this browser.'}
                  trigger={
                    <select
                      aria-label={interfaceText("RustyMilk preset library")}
                      className="player-visualizer-native-library"
                      data-testid="visualizer-native-preset-library"
                      onChange={loadRustyMilkLibraryPreset}
                      value={selectedRustyMilkPresetValue}
                     {...interfaceTextProps("RustyMilk preset library")}>
                      <option value="">
                        {visibleRustyMilkPresetLibrary.length === 0 ? interfaceText("No matches") : (
                          rustyMilkLibraryMode === 'favorites' ? interfaceText('Favorites') : interfaceText('Presets')
                        )}
                      </option>
                      {visibleRustyMilkPresetLibrary.map((preset) => (
                        <option key={preset.id} value={preset.id}>
                          {rustyMilkFavoritePresetIds.includes(preset.id) ? `${interfaceText("(favorite)")} ` : ''}
                          {preset.title || preset.fileName}
                        </option>
                      ))}
                    </select>
                  }
                />
              ) : null}
              {rustyMilkPresetLibrary.length > 0 ? (
                <LocalizedPopup
                  content={activeRustyMilkPresetIsFavorite
                    ? 'Remove the active RustyMilk preset from favorites.'
                    : 'Mark the active RustyMilk preset as a favorite.'}
                  trigger={
                    <Button
                      aria-label={
                        activeRustyMilkPresetIsFavorite
                          ? interfaceText('Unfavorite active RustyMilk preset')
                          : interfaceText('Favorite active RustyMilk preset')
                      }
                      active={activeRustyMilkPresetIsFavorite}
                      data-testid="visualizer-toggle-native-favorite"
                      disabled={!activeRustyMilkPresetId}
                      icon
                      onClick={toggleRustyMilkPresetFavorite}
                      size="mini"
                    >
                      <Icon name={activeRustyMilkPresetIsFavorite ? 'star' : 'star outline'} />
                    </Button>
                  }
                />
              ) : null}
              {rustyMilkPresetLibrary.length > 0 ? (
                <LocalizedPopup
                  content={rustyMilkLibraryMode === 'favorites'
                    ? 'Show all imported RustyMilk presets.'
                    : 'Show only favorite RustyMilk presets.'}
                  trigger={
                    <Button
                      aria-label={
                        rustyMilkLibraryMode === 'favorites'
                          ? interfaceText('Show all RustyMilk presets')
                          : interfaceText('Show favorite RustyMilk presets')
                      }
                      active={rustyMilkLibraryMode === 'favorites'}
                      data-testid="visualizer-toggle-native-favorites-only"
                      disabled={rustyMilkFavoritePresetIds.length === 0}
                      icon
                      onClick={toggleRustyMilkLibraryMode}
                      size="mini"
                    >
                      <Icon name="filter" />
                    </Button>
                  }
                />
              ) : null}
              {rustyMilkPresetLibrary.length > 1 ? (
                <Popup
                  content={interfaceText("Return to the previous RustyMilk preset, or move backward in the local preset library.")}
                  trigger={
                    <Button
                      aria-label={interfaceText("Previous RustyMilk preset")}
                      data-testid="visualizer-previous-native-preset"
                      disabled={visibleRustyMilkPresetLibrary.length === 0}
                      icon
                      onClick={previousRustyMilkLibraryPreset}
                      size="mini"
                     {...interfaceTextProps("Previous RustyMilk preset")}>
                      <Icon name="step backward" />
                    </Button>
                  }
                 {...interfaceTextProps("Return to the previous RustyMilk preset, or move backward in the local preset library.")}/>
              ) : null}
              {rustyMilkPresetLibrary.length > 1 ? (
                <Popup
                  content={interfaceText("Jump to a random imported RustyMilk preset from this browser.")}
                  trigger={
                    <Button
                      aria-label={interfaceText("Random imported RustyMilk preset")}
                      data-testid="visualizer-random-native-preset"
                      disabled={visibleRustyMilkPresetLibrary.length === 0}
                      icon
                      onClick={randomRustyMilkLibraryPreset}
                      size="mini"
                     {...interfaceTextProps("Random imported RustyMilk preset")}>
                      <Icon name="random" />
                    </Button>
                  }
                 {...interfaceTextProps("Jump to a random imported RustyMilk preset from this browser.")}/>
              ) : null}
              {rustyMilkPresetLibrary.length > 0 ? (
                <Popup
                  content={interfaceText("Remove the selected RustyMilk preset from this browser.")}
                  trigger={
                    <Button
                      aria-label={interfaceText("Remove selected RustyMilk preset")}
                      data-testid="visualizer-remove-native-preset"
                      disabled={!activeRustyMilkPresetId}
                      icon
                      onClick={removeActiveRustyMilkPreset}
                      size="mini"
                     {...interfaceTextProps("Remove selected RustyMilk preset")}>
                      <Icon name="minus circle" />
                    </Button>
                  }
                 {...interfaceTextProps("Remove the selected RustyMilk preset from this browser.")}/>
              ) : null}
              {rustyMilkPresetLibrary.length > 0 ? (
                <Popup
                  content={interfaceText("Clear imported RustyMilk presets from this browser.")}
                  trigger={
                    <Button
                      aria-label={interfaceText("Clear imported RustyMilk presets")}
                      data-testid="visualizer-clear-native-preset-library"
                      icon
                      onClick={clearRustyMilkPresetLibrary}
                      size="mini"
                     {...interfaceTextProps("Clear imported RustyMilk presets")}>
                      <Icon name="trash alternate outline" />
                    </Button>
                  }
                 {...interfaceTextProps("Clear imported RustyMilk presets from this browser.")}/>
              ) : null}
              <Popup
                content={interfaceText("Import a local .milk or .milk2 preset into the RustyMilk renderer.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Import RustyMilk preset")}
                    data-testid="visualizer-import-native-preset"
                    icon
                    onClick={() => fileInputRef.current?.click()}
                    size="mini"
                   {...interfaceTextProps("Import RustyMilk preset")}>
                    <Icon name="upload" />
                  </Button>
                }
               {...interfaceTextProps("Import a local .milk or .milk2 preset into the RustyMilk renderer.")}/>
              <Popup
                content={interfaceText("Import a RustyMilk preset folder with its local image assets.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Import RustyMilk preset folder")}
                    data-testid="visualizer-import-native-preset-folder"
                    icon
                    onClick={() => directoryInputRef.current?.click()}
                    size="mini"
                   {...interfaceTextProps("Import RustyMilk preset folder")}>
                    <Icon name="folder open outline" />
                  </Button>
                }
               {...interfaceTextProps("Import a RustyMilk preset folder with its local image assets.")}/>
              <Popup
                content={interfaceText("Choose a global RustyMilk parameter to edit on the active preset.")}
                trigger={
                  <select
                    aria-label={interfaceText("RustyMilk editable parameter")}
                    className="player-visualizer-native-library"
                    data-testid="visualizer-native-parameter"
                    onChange={selectRustyMilkParameter}
                    value={selectedRustyMilkParameter}
                   {...interfaceTextProps("RustyMilk editable parameter")}>
                    {nativeEditableParameters.map((parameter) => (
                      <option key={parameter.key} value={parameter.key}>
                        {parameter.label}
                      </option>
                    ))}
                  </select>
                }
               {...interfaceTextProps("Choose a global RustyMilk parameter to edit on the active preset.")}/>
              <LocalizedPopup
                content="Adjust {label} for the active RustyMilk preset before applying the edited copy locally."
                parameters={{ label: rustyMilkParameter.label.toLowerCase() }}
                trigger={
                  <input
                    aria-label={interfaceText("Adjust RustyMilk {label}", { "label": (rustyMilkParameter.label) })}
                    className="player-visualizer-native-range"
                    data-testid="visualizer-native-parameter-value"
                    max={rustyMilkParameter.max}
                    min={rustyMilkParameter.min}
                    onChange={updateRustyMilkParameterDraft}
                    step={rustyMilkParameter.step}
                    type="range"
                    value={rustyMilkParameterValue}
                   {...interfaceTextProps("Adjust RustyMilk {label}")}/>
                }
              />
              <Popup
                content={interfaceText("Apply the selected RustyMilk parameter value and save the edited preset in this browser.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Apply RustyMilk parameter edit")}
                    data-testid="visualizer-apply-native-parameter"
                    icon
                    onClick={applyRustyMilkParameterEdit}
                    size="mini"
                   {...interfaceTextProps("Apply RustyMilk parameter edit")}>
                    <Icon name="sliders horizontal" />
                  </Button>
                }
               {...interfaceTextProps("Apply the selected RustyMilk parameter value and save the edited preset in this browser.")}/>
              <Popup
                content={interfaceText("Randomize the active RustyMilk preset's common visual parameters and save the edited copy locally.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Randomize RustyMilk visual parameters")}
                    data-testid="visualizer-randomize-native-parameters"
                    icon
                    onClick={randomizeRustyMilkPresetParameters}
                    size="mini"
                   {...interfaceTextProps("Randomize RustyMilk visual parameters")}>
                    <Icon name="shuffle" />
                  </Button>
                }
               {...interfaceTextProps("Randomize the active RustyMilk preset's common visual parameters and save the edited copy locally.")}/>
              <Popup
                content={interfaceText("Show or hide RustyMilk debug details for the active preset.")}
                trigger={
                  <Button
                    {...interfaceTextAttributes(showNativeDebug ? 'Hide RustyMilk debug details' : 'Show RustyMilk debug details')}
                    active={showNativeDebug}
                    data-testid="visualizer-toggle-native-debug"
                    icon
                    onClick={() => setShowNativeDebug((current) => !current)}
                    size="mini"
                  >
                    <Icon name="bug" />
                  </Button>
                }
               {...interfaceTextProps("Show or hide RustyMilk debug details for the active preset.")}/>
              <Popup
                content={interfaceText("Cap RustyMilk rendering for lower GPU load, or leave it uncapped for maximum smoothness.")}
                trigger={
                  <select
                    aria-label={interfaceText("RustyMilk FPS cap")}
                    className="player-visualizer-native-library"
                    data-testid="visualizer-native-fps-cap"
                    onChange={updateNativeFpsCap}
                    value={nativeFpsCap}
                   {...interfaceTextProps("RustyMilk FPS cap")}>
                    <option value="full">{interfaceText("Full FPS")}</option>
                    <option value="60">{interfaceText("60 FPS")}</option>
                    <option value="30">{interfaceText("30 FPS")}</option>
                    <option value="24">{interfaceText("24 FPS")}</option>
                  </select>
                }
               {...interfaceTextProps("Cap RustyMilk rendering for lower GPU load, or leave it uncapped for maximum smoothness.")}/>
              <Popup
                content={interfaceText("Choose a RustyMilk quality preset. Efficient lowers GPU load, Balanced caps at 60 FPS, and Full leaves rendering uncapped.")}
                trigger={
                  <select
                    aria-label={interfaceText("RustyMilk quality preset")}
                    className="player-visualizer-native-library"
                    data-testid="visualizer-native-quality"
                    onChange={updateNativeQualityPreset}
                    value={nativeQualityPreset}
                   {...interfaceTextProps("RustyMilk quality preset")}>
                    <option value="balanced">{interfaceText("Balanced")}</option>
                    <option value="efficient">{interfaceText("Efficient")}</option>
                    <option value="full">{interfaceText("Full")}</option>
                    <option value="custom">{interfaceText("Custom")}</option>
                  </select>
                }
               {...interfaceTextProps("Choose a RustyMilk quality preset. Efficient lowers GPU load, Balanced caps at 60 FPS, and Full leaves rendering uncapped.")}/>
              <Popup
                content={interfaceText("Export the active RustyMilk preset text after any local edits.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Export active RustyMilk preset")}
                    data-testid="visualizer-export-native-preset"
                    icon
                    onClick={exportRustyMilkPreset}
                    size="mini"
                   {...interfaceTextProps("Export active RustyMilk preset")}>
                    <Icon name="file alternate outline" />
                  </Button>
                }
               {...interfaceTextProps("Export the active RustyMilk preset text after any local edits.")}/>
              <Popup
                content={interfaceText("Choose which custom shape from the active RustyMilk preset should be exported or removed.")}
                trigger={
                  <select
                    aria-label={interfaceText("RustyMilk shape fragment")}
                    className="player-visualizer-native-library"
                    data-testid="visualizer-native-shape-fragment"
                    disabled={!hasNativeShapes}
                    onChange={(event) => setSelectedNativeShapeIndex(Number(event.target.value))}
                    value={hasNativeShapes ? selectedNativeShapeIndex : 0}
                   {...interfaceTextProps("RustyMilk shape fragment")}>
                    {hasNativeShapes ? rustyMilkFragmentSummary.shapes.map((shape) => (
                      <option key={shape.index} value={shape.index}>
                        {shape.label}
                      </option>
                    )) : (
                      <option value={0}>{interfaceText("No shapes")}</option>
                    )}
                  </select>
                }
               {...interfaceTextProps("Choose which custom shape from the active RustyMilk preset should be exported or removed.")}/>
              <Popup
                content={interfaceText("Export the selected custom shape in the active RustyMilk preset as a .shape fragment.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Export RustyMilk shape fragment")}
                    data-testid="visualizer-export-native-shape"
                    disabled={!hasNativeShapes}
                    icon
                    onClick={() => exportRustyMilkFragment('shape')}
                    size="mini"
                   {...interfaceTextProps("Export RustyMilk shape fragment")}>
                    <Icon name="download" />
                  </Button>
                }
               {...interfaceTextProps("Export the selected custom shape in the active RustyMilk preset as a .shape fragment.")}/>
              <Popup
                content={interfaceText("Remove the selected custom shape from the active RustyMilk preset and persist the edited copy locally.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Remove RustyMilk shape fragment")}
                    data-testid="visualizer-remove-native-shape"
                    disabled={!hasNativeShapes}
                    icon
                    onClick={() => removeRustyMilkFragment('shape')}
                    size="mini"
                   {...interfaceTextProps("Remove RustyMilk shape fragment")}>
                    <Icon name="erase" />
                  </Button>
                }
               {...interfaceTextProps("Remove the selected custom shape from the active RustyMilk preset and persist the edited copy locally.")}/>
              <Popup
                content={interfaceText("Choose which custom wave from the active RustyMilk preset should be exported or removed.")}
                trigger={
                  <select
                    aria-label={interfaceText("RustyMilk wave fragment")}
                    className="player-visualizer-native-library"
                    data-testid="visualizer-native-wave-fragment"
                    disabled={!hasNativeWaves}
                    onChange={(event) => setSelectedNativeWaveIndex(Number(event.target.value))}
                    value={hasNativeWaves ? selectedNativeWaveIndex : 0}
                   {...interfaceTextProps("RustyMilk wave fragment")}>
                    {hasNativeWaves ? rustyMilkFragmentSummary.waves.map((wave) => (
                      <option key={wave.index} value={wave.index}>
                        {wave.label}
                      </option>
                    )) : (
                      <option value={0}>{interfaceText("No waves")}</option>
                    )}
                  </select>
                }
               {...interfaceTextProps("Choose which custom wave from the active RustyMilk preset should be exported or removed.")}/>
              <Popup
                content={interfaceText("Export the selected custom wave in the active RustyMilk preset as a .wave fragment.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Export RustyMilk wave fragment")}
                    data-testid="visualizer-export-native-wave"
                    disabled={!hasNativeWaves}
                    icon
                    onClick={() => exportRustyMilkFragment('wave')}
                    size="mini"
                   {...interfaceTextProps("Export RustyMilk wave fragment")}>
                    <Icon name="download" />
                  </Button>
                }
               {...interfaceTextProps("Export the selected custom wave in the active RustyMilk preset as a .wave fragment.")}/>
              <Popup
                content={interfaceText("Remove the selected custom wave from the active RustyMilk preset and persist the edited copy locally.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Remove RustyMilk wave fragment")}
                    data-testid="visualizer-remove-native-wave"
                    disabled={!hasNativeWaves}
                    icon
                    onClick={() => removeRustyMilkFragment('wave')}
                    size="mini"
                   {...interfaceTextProps("Remove RustyMilk wave fragment")}>
                    <Icon name="erase" />
                  </Button>
                }
               {...interfaceTextProps("Remove the selected custom wave from the active RustyMilk preset and persist the edited copy locally.")}/>
              <LocalizedPopup
                content="Native automatic preset changes: {mode}. Beat mode advances after repeated detected bass beats; timed mode advances on an interval."
                parameters={{ mode: interfaceText(getRustyMilkAutomationLabel(rustyMilkAutomationMode)) }}
                trigger={
                  <Button
                    aria-label={interfaceText('Native automatic preset changes: {mode}', {
                      mode: interfaceText(getRustyMilkAutomationLabel(rustyMilkAutomationMode)),
                    })}
                    active={rustyMilkAutomationMode !== 'off'}
                    data-testid="visualizer-native-automation"
                    icon
                    onClick={cycleRustyMilkAutomationMode}
                    size="mini"
                  >
                    <Icon name={rustyMilkAutomationMode === 'beat' ? 'heartbeat' : 'clock outline'} />
                  </Button>
                }
              />
              {rustyMilkAutomationMode === 'beat' ? (
                <Popup
                  content={interfaceText("Choose how many detected bass beats should pass before RustyMilk advances to another preset.")}
                  trigger={
                    <select
                      aria-label={interfaceText("RustyMilk beats per preset")}
                      className="player-visualizer-native-library"
                      data-testid="visualizer-native-automation-beats"
                      onChange={updateRustyMilkAutomationBeats}
                      value={rustyMilkAutomationSettings.beatsPerPreset}
                     {...interfaceTextProps("RustyMilk beats per preset")}>
                      <option value={4}>{interfaceText("4 beats")}</option>
                      <option value={8}>{interfaceText("8 beats")}</option>
                      <option value={16}>{interfaceText("16 beats")}</option>
                    </select>
                  }
                 {...interfaceTextProps("Choose how many detected bass beats should pass before RustyMilk advances to another preset.")}/>
              ) : null}
              {rustyMilkAutomationMode === 'timed' ? (
                <Popup
                  content={interfaceText("Choose how long RustyMilk should wait before timed preset changes.")}
                  trigger={
                    <select
                      aria-label={interfaceText("RustyMilk timed preset interval")}
                      className="player-visualizer-native-library"
                      data-testid="visualizer-native-automation-interval"
                      onChange={updateRustyMilkAutomationInterval}
                      value={rustyMilkAutomationSettings.timedIntervalSeconds}
                     {...interfaceTextProps("RustyMilk timed preset interval")}>
                    <option value={15}>{interfaceText("15 sec")}</option>
                    <option value={30}>{interfaceText("30 sec")}</option>
                    <option value={60}>{interfaceText("60 sec")}</option>
                    </select>
                  }
                 {...interfaceTextProps("Choose how long RustyMilk should wait before timed preset changes.")}/>
              ) : null}
            </>
          ) : null}
          <LocalizedPopup
            content={nativeBankNavigationDisabled
              ? 'No imported RustyMilk presets match the current filter.'
              : 'Load a different RustyMilk preset.'}
            trigger={
              <Button
                aria-label={interfaceText("Next visualizer preset")}
                data-testid="visualizer-next-preset"
                disabled={nativeBankNavigationDisabled}
                icon
                onClick={cyclePreset}
                size="mini"
               {...interfaceTextProps("Next visualizer preset")}>
                <Icon name="random" />
              </Button>
            }
          />
          {mode === 'inline' && !compactControls ? (
            <>
              <Popup
                content={interfaceText("Expand visualizer to fill the browser window.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Expand visualizer to full browser window")}
                    data-testid="visualizer-fullwindow"
                    icon
                    onClick={() => onModeChange('fullwindow')}
                    size="mini"
                   {...interfaceTextProps("Expand visualizer to full browser window")}>
                    <Icon name="expand arrows alternate" />
                  </Button>
                }
               {...interfaceTextProps("Expand visualizer to fill the browser window.")}/>
              <Popup
                content={interfaceText("Enter true fullscreen.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Enter fullscreen visualizer")}
                    data-testid="visualizer-fullscreen"
                    icon
                    onClick={enterFullscreen}
                    size="mini"
                   {...interfaceTextProps("Enter fullscreen visualizer")}>
                    <Icon name="expand" />
                  </Button>
                }
               {...interfaceTextProps("Enter true fullscreen.")}/>
            </>
          ) : mode === 'inline' ? null : (
            <>
              {mode === 'fullwindow' ? (
                <Popup
                  content={interfaceText("Enter true fullscreen.")}
                  trigger={
                    <Button
                      aria-label={interfaceText("Enter fullscreen visualizer")}
                      data-testid="visualizer-fullscreen"
                      icon
                      onClick={enterFullscreen}
                      size="mini"
                     {...interfaceTextProps("Enter fullscreen visualizer")}>
                      <Icon name="expand" />
                    </Button>
                  }
                 {...interfaceTextProps("Enter true fullscreen.")}/>
              ) : null}
              <Popup
                content={interfaceText("Return visualizer to the player bar.")}
                trigger={
                  <Button
                    aria-label={interfaceText("Collapse visualizer")}
                    data-testid="visualizer-collapse"
                    icon
                    onClick={exitFullscreen}
                    size="mini"
                   {...interfaceTextProps("Collapse visualizer")}>
                    <Icon name="compress" />
                  </Button>
                }
               {...interfaceTextProps("Return visualizer to the player bar.")}/>
            </>
          )}
        </div>
  );
};

export default VisualizerOverlayControls;
