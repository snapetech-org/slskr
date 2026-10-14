import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../../lib/interfaceLocale";
import { getPlayerRatingSummary } from '../../lib/playerRatings';
import { Icon, Popup } from 'semantic-ui-react';

const PlayerRatingControls = ({ current, onChange, rating }) => {
  useInterfaceLanguage();
  if (!current) return null;

  const summary = getPlayerRatingSummary(current);

  return (
    <div
      aria-label={interfaceText("Now playing rating")}
      className={[
        'player-rating-controls',
        `player-rating-controls-${summary.tone}`,
      ].join(' ')}
      data-testid="player-rating-controls"
      role="group"
     {...interfaceTextProps("Now playing rating")}>
      {[1, 2, 3, 4, 5].map((value) => (
        <Popup
          content={
            value === rating
              ? 'Clear this local rating.'
              : `Rate this track ${value} out of 5 for local discovery context.`
          }
          key={value}
          trigger={
            <button
              aria-label={
                value === rating
                  ? `Clear ${value} star rating`
                  : `Rate ${value} stars`
              }
              className={[
                'player-rating-button',
                value <= rating ? 'player-rating-button-active' : '',
              ].filter(Boolean).join(' ')}
              data-testid={`player-rating-${value}`}
              onClick={() => onChange(value === rating ? 0 : value)}
              title={
                value === rating
                  ? 'Clear this local rating.'
                  : `Rate this track ${value} out of 5.`
              }
              type="button"
            >
              <Icon name={value <= rating ? 'star' : 'star outline'} />
            </button>
          }
        />
      ))}
      <span className="player-rating-summary">{interfaceText(summary.label)}</span>
    </div>
  );
};

export default PlayerRatingControls;
