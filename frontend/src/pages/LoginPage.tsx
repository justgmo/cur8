import { useAuth } from '../contexts/AuthContext';

export function LoginPage() {
  const { login } = useAuth();

  return (
    <div>
      <h1>Cur8</h1>
      <p>Swipe through your Spotify liked songs.</p>
      <button type="button" onClick={login}>
        Log in with Spotify
      </button>
    </div>
  );
}
