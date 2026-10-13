import { NavLink } from 'react-router-dom';
import { Dropdown, Icon, Menu } from 'semantic-ui-react';
import { useInterfaceLanguage } from '../lib/interfaceLocale';

const NavigationIcon = ({ alert, alertTestId, name }) => {
  const { t, languageFor, directionFor } = useInterfaceLanguage();
  return (
  <span className="navigation-alert-icon">
    <Icon name={name} />
    {alert && (
      <span
        aria-label={t('New activity')}
        lang={languageFor('New activity')}
        dir={directionFor('New activity')}
        className="navigation-alert-dot"
        data-testid={alertTestId}
        role="status"
      />
    )}
  </span>
  );
};

const AppNavigationPrimary = ({
  isAgent,
  isLegacyProfile,
  isNativeProfile,
  navActivity,
  version,
}) => {
  const { t, languageFor, directionFor } = useInterfaceLanguage();
  const label = (source) => (
    <span lang={languageFor(source)} dir={directionFor(source)}>
      {t(source)}
    </span>
  );
  return (
              <div
                aria-label={t('Primary navigation')}
                className="navigation-primary"
                lang={languageFor('Primary navigation')}
                dir={directionFor('Primary navigation')}
                role="navigation"
              >
                {version.isCanary && (
                  <Menu.Item>
                    <Icon
                      color="yellow"
                      name="flask"
                    />
                    {label('Canary')}
                  </Menu.Item>
                )}
              {isAgent ? (
                <Menu.Item>
                  <Icon name="detective" />
                  {label('Agent Mode')}
                </Menu.Item>
              ) : (
                isLegacyProfile ? (
                <>
                  <NavLink to="/dashboard">
                    <Menu.Item data-testid="nav-dashboard">
                      <Icon name="chart bar" />
                      {label('Dashboard')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/searches">
                    <Menu.Item data-testid="nav-search">
                      <Icon name="search" />
                      {label('Search')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/downloads">
                    <Menu.Item data-testid="nav-downloads">
                      <Icon name="download" />
                      {label('Downloads')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/uploads">
                    <Menu.Item data-testid="nav-uploads">
                      <Icon name="upload" />
                      {label('Uploads')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/rooms">
                    <Menu.Item data-testid="nav-rooms">
                      <NavigationIcon
                        alert={navActivity.rooms}
                        alertTestId="nav-rooms-alert"
                        name="comments"
                      />
                      {label('Rooms')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/chat">
                    <Menu.Item data-testid="nav-chat">
                      <NavigationIcon
                        alert={navActivity.chat}
                        alertTestId="nav-chat-alert"
                        name="comment"
                      />
                      {label('Chat')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/users">
                    <Menu.Item data-testid="nav-users">
                      <Icon name="users" />
                      {label('Users')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/browse">
                    <Menu.Item data-testid="nav-browse">
                      <Icon name="folder open" />
                      {label('Browse')}
                    </Menu.Item>
                  </NavLink>
                </>
                ) : isNativeProfile ? (
                <>
                  <NavLink to="/searches">
                    <Menu.Item data-testid="nav-search">
                      <Icon name="search" />
                      {label('Search')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/discovery-graph">
                    <Menu.Item data-testid="nav-discovery-graph">
                      <Icon name="crosshairs" />
                      {label('Discovery Graph')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/playlist-intake">
                    <Menu.Item data-testid="nav-playlist-intake">
                      <Icon name="list alternate outline" />
                      {label('Playlist Intake')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/wishlist">
                    <Menu.Item data-testid="nav-wishlist">
                      <Icon name="star" />
                      {label('Wishlist')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/lidarr">
                    <Menu.Item data-testid="nav-lidarr">
                      <Icon name="music" />
                      {label('Lidarr')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/downloads">
                    <Menu.Item data-testid="nav-downloads">
                      <Icon name="download" />
                      {label('Downloads')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/uploads">
                    <Menu.Item data-testid="nav-uploads">
                      <Icon name="upload" />
                      {label('Uploads')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/messages">
                    <Menu.Item data-testid="nav-messages">
                      <NavigationIcon
                        alert={navActivity.rooms || navActivity.chat}
                        alertTestId={
                          navActivity.chat ? 'nav-chat-alert' : 'nav-rooms-alert'
                        }
                        name="comments"
                      />
                      {label('Messages')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/users">
                    <Menu.Item data-testid="nav-users">
                      <Icon name="users" />
                      {label('Users')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/contacts">
                    <Menu.Item data-testid="nav-contacts">
                      <Icon name="address book" />
                      {label('Contacts')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/solid">
                    <Menu.Item data-testid="nav-solid">
                      <Icon name="key" />
                      {label('Solid')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/collections">
                    <Menu.Item data-testid="nav-collections">
                      <Icon name="list" />
                      {label('Collections')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/sharegroups">
                    <Menu.Item data-testid="nav-groups">
                      <Icon name="users" />
                      {label('Share Groups')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/shared">
                    <Menu.Item data-testid="nav-shared-with-me">
                      <Icon name="share" />
                      {label('Shared with Me')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/browse">
                    <Menu.Item data-testid="nav-browse">
                      <Icon name="folder open" />
                      {label('Browse')}
                    </Menu.Item>
                  </NavLink>
                </>
                ) : (
                <>
                  <NavLink to="/searches">
                    <Menu.Item data-testid="nav-search">
                      <Icon name="search" />
                      {label('Search')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/wishlist">
                    <Menu.Item data-testid="nav-wishlist">
                      <Icon name="star" />
                      {label('Wishlist')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/downloads">
                    <Menu.Item data-testid="nav-downloads">
                      <Icon name="download" />
                      {label('Downloads')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/uploads">
                    <Menu.Item data-testid="nav-uploads">
                      <Icon name="upload" />
                      {label('Uploads')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/messages">
                    <Menu.Item data-testid="nav-messages">
                      <NavigationIcon
                        alert={navActivity.rooms || navActivity.chat}
                        alertTestId={
                          navActivity.chat ? 'nav-chat-alert' : 'nav-rooms-alert'
                        }
                        name="comments"
                      />
                      {label('Messages')}
                    </Menu.Item>
                  </NavLink>
                  <NavLink to="/users">
                    <Menu.Item data-testid="nav-users">
                      <Icon name="users" />
                      {label('Users')}
                    </Menu.Item>
                  </NavLink>
                  <Dropdown
                    aria-label={t('More navigation options')}
                    className="navigation-more"
                    data-testid="nav-more"
                    dir={directionFor('More navigation options')}
                    icon={null}
                    item
                    lang={languageFor('More navigation options')}
                    trigger={(
                      <span className="navigation-more-trigger">
                        <Icon name="ellipsis horizontal" />
                        {label('More')}
                      </span>
                    )}
                  >
                    <Dropdown.Menu>
                      <Dropdown.Item
                        as={NavLink}
                        data-testid="nav-discovery-graph"
                        icon="crosshairs"
                        text={label('Discovery Graph')}
                        to="/discovery-graph"
                      />
                      <Dropdown.Item
                        as={NavLink}
                        data-testid="nav-playlist-intake"
                        icon="list alternate outline"
                        text={label('Playlist Intake')}
                        to="/playlist-intake"
                      />
                      <Dropdown.Item
                        as={NavLink}
                        data-testid="nav-contacts"
                        icon="address book"
                        text={label('Contacts')}
                        to="/contacts"
                      />
                      <Dropdown.Item
                        as={NavLink}
                        data-testid="nav-solid"
                        icon="key"
                        text={label('Solid')}
                        to="/solid"
                      />
                      <Dropdown.Item
                        as={NavLink}
                        data-testid="nav-collections"
                        icon="list"
                        text={label('Collections')}
                        to="/collections"
                      />
                      <Dropdown.Item
                        as={NavLink}
                        data-testid="nav-groups"
                        icon="users"
                        text={label('Share Groups')}
                        to="/sharegroups"
                      />
                      <Dropdown.Item
                        as={NavLink}
                        data-testid="nav-shared-with-me"
                        icon="share"
                        text={label('Shared with Me')}
                        to="/shared"
                      />
                      <Dropdown.Item
                        as={NavLink}
                        data-testid="nav-browse"
                        icon="folder open"
                        text={label('Browse')}
                        to="/browse"
                      />
                    </Dropdown.Menu>
                  </Dropdown>
                </>
                )
              )}
            </div>
  );
};

export default AppNavigationPrimary;
