import { useRef, useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./Form.css";
import Bubbles from "./bubbles";
import { auth } from "./firebase/firebase"; // Import your Firebase auth
import { signInWithEmailAndPassword } from "firebase/auth";

const Login = () => {
  const userRef = useRef();
  const errRef = useRef();
  const navigate = useNavigate(); // To navigate to Home.jsx

  const [user, setUser] = useState("");
  const [pwd, setPwd] = useState("");
  const [errMsg, setErrMsg] = useState("");
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    userRef.current.focus();
  }, []);

  useEffect(() => {
    setErrMsg("");
  }, [user, pwd]);

  useEffect(() => {
    setUser("");
    setPwd("");
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const userCredential = await signInWithEmailAndPassword(auth, user, pwd);
      console.log("User logged in: ", userCredential.user);
      setSuccess(true);
      navigate("/home"); // Redirect to Home.jsx
    } catch (error) {
      console.error("Error logging in: ", error);
      setErrMsg("Invalid username or password");
      errRef.current.focus();
    }
  };

  return (
    <>
      <div className="split-screen">
        <div className="left">
          <h1>Knowledge Nuggets</h1>
          <div className="info">
            <h2>AI Video Summarization Tool for Learning</h2>
            <br />
            <p>
              Knowledge Nuggets uses a customized AI to increase your efficiency
              in learning
            </p>
          </div>
        </div>
        <div className="right">
          <section>
            <p
              ref={errRef}
              className={errMsg ? "errmsg" : "offscreen"}
              aria-live="assertive"
            >
              {errMsg}
            </p>
            <h1>Login</h1>
            <form onSubmit={handleSubmit} autoComplete="off">
              <label htmlFor="username">Email:</label>
              <input
                type="text"
                id="username"
                ref={userRef}
                autoComplete="off"
                onChange={(e) => setUser(e.target.value)}
                value={user}
                required
              />

              <label htmlFor="password">Password:</label>
              <input
                type="password"
                id="password"
                autoComplete="off"
                onChange={(e) => setPwd(e.target.value)}
                value={pwd}
                required
              />
              <button>Sign In</button>
            </form>
            <p className="need-account">
              Need an Account?
              <br />
              <Link to="/register" className="sign-up-button">
                Sign Up
              </Link>
            </p>
          </section>
        </div>
      </div>
    </>
  );
};

export default Login;
