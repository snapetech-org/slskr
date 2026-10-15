import LocalizedText from "./Shared/LocalizedText";
import { interfaceText, interfaceTextProps, useInterfaceLanguage } from "../lib/interfaceLocale";
import Footer from './Shared/Footer';
import { urlBase } from '../config';
import { toDisplayError } from '../lib/errors';
import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  Button,
  Form,
  Grid,
  Header,
  Icon,
  Input,
  Message,
  Segment,
} from 'semantic-ui-react';

const initialState = {
  password: '',
  username: '',
};

export const getHttpsHintUrl = (location) => {
  if (!location) {
    return null;
  }

  const { hostname, protocol } = location;

  if (!hostname || protocol === 'https:') {
    return null;
  }

  return `https://${hostname}:5031`;
};

const LoginForm = ({ error, loading, onLoginAttempt }) => {
  useInterfaceLanguage();
  const usernameInput = useRef();
  const [state, setState] = useState(initialState);
  const [ready, setReady] = useState(false);
  const httpsUrl = useMemo(() => {
    if (typeof window === 'undefined') {
      return null;
    }

    return getHttpsHintUrl(window.location);
  }, []);

  useEffect(() => {
    if (state.username.trim() !== '' && state.password !== '') {
      setReady(true);
    } else {
      setReady(false);
    }
  }, [state]);

  useEffect(() => {
    usernameInput.current?.focus();
  }, [loading]);

  const handleChange = (field, value) => {
    setState((currentState) => ({
      ...currentState,
      [field]: value,
    }));
  };

  const { password, username } = state;

  return (
    <>
      <Grid
        style={{ height: 'calc(100vh - 40px)' }}
        textAlign="center"
        verticalAlign="middle"
      >
        <Grid.Column style={{ maxWidth: 460 }}>
          <Header
            as="h2"
            style={{
              marginBottom: '1.25rem',
            }}
            textAlign="center"
          >
            <img
              alt={interfaceText("slskr")}
              src={`${urlBase}/slskr-logo.png`}
              style={{
                display: 'inline-block',
                height: 'auto',
                maxWidth: '320px',
                width: '80%',
              }}
             {...interfaceTextProps("slskr")}/>
          </Header>
          <Form size="large">
            <Segment raised>
              <Input
                data-testid="login-username"
                disabled={loading}
                fluid
                icon="user"
                iconPosition="left"
                onChange={(event) =>
                  handleChange('username', event.target.value)
                }
                placeholder={interfaceText("Username")}
                ref={usernameInput}
                value={username}
               {...interfaceTextProps("Username")}/>
              <Form.Input
                data-testid="login-password"
                disabled={loading}
                fluid
                icon="lock"
                iconPosition="left"
                onChange={(event) =>
                  handleChange('password', event.target.value)
                }
                placeholder={interfaceText("Password")}
                type="password"
                value={password}
               {...interfaceTextProps("Password")}/>
            </Segment>
            <Button
              className="login-button"
              data-testid="login-submit"
              disabled={!ready || loading}
              fluid
              loading={loading}
              onClick={() => onLoginAttempt(username, password)}
              primary
              size="large"
            >
              <Icon name="sign in" />
              <LocalizedText source={"Login"} /></Button>
            {error && (
              <Message
                className="login-failure"
                floating
                negative
              >
                <Icon name="x" />
                {toDisplayError(error, interfaceText('Login failed'))}
              </Message>
            )}
            {httpsUrl && (
              <Message
                className="login-https-hint"
                icon
                info
                size="small"
              >
                <Icon name="shield alternate" />
                <Message.Content>
                  <Message.Header><LocalizedText source={"HTTPS Option"} /></Message.Header>
                  <LocalizedText source={"If your instance exposes TLS, sign in securely at"} />{' '}
                  <a className="login-https-hint-link" href={httpsUrl}>
                    {httpsUrl}
                  </a>.
                </Message.Content>
              </Message>
            )}
          </Form>
        </Grid.Column>
      </Grid>
      <Footer />
    </>
  );
};

export default LoginForm;
