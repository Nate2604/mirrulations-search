import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getAuthStatus } from "../api/searchApi";
import "../styles/Home.css";

import hero from '../assets/hero.jpg'

export default function Home() {
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);

  useEffect(() => {
    getAuthStatus()
      .then((data) => {
        if (data.logged_in) {
          setUser({ name: data.name, email: data.email });
        }
      })
      .finally(() => setAuthLoading(false));
  }, []);

  return (

  <div className="home-page">
      <div className="hero-img">
        <div className="hero-text-container">
          <h1>Mirrulations<br/>Open Regulatory Data</h1>
          <p>Mirrulations mirrors millions of U.S. federal regulatory documents and delivers them in a structured format designed for transparency, scale, and analysis.</p>
          <div className="hero-buttons"><button className="private-btn">Private Policy</button>
            <button className="homesearch-btn">Search Dockets</button></div>

        </div>
      </div>
    </div>
  );
}
