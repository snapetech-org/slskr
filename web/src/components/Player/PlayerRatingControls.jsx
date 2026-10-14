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
          content={interfaceText(
            value === rating
              ? "Clear this local rating."
              : "Rate this track {stars} out of 5 for local discovery context.",
            { "stars": (value) },
          )}
          key={value}
          trigger={
            <button
              className={[
                'player-rating-button',
                value <= rating ? 'player-rating-button-active' : '',
              ].filter(Boolean).join(' ')}
              data-testid={`player-rating-${value}`}
              onClick={() => onChange(value === rating ? 0 : value)}
              type="button"
             {...interfaceTextProps(
               value === rating ? "Clear rating ({stars}/5)" : "Set rating to {stars} out of 5",
               { "stars": (value) },
             )}
              title={interfaceText(
                value === rating ? "Clear this local rating." : "Rate this track {stars} out of 5.",
                { "stars": (value) },
              )}
            >
              <Icon name={value <= rating ? 'star' : 'star outline'} />
            </button>
          }
         {...interfaceTextProps(
           value === rating
             ? "Clear this local rating."
             : "Rate this track {stars} out of 5 for local discovery context.",
           { "stars": (value) },
         )}
        />
      ))}
      <span className="player-rating-summary">{interfaceText(summary.label)}</span>
    </div>
  );
};

export default PlayerRatingControls;
