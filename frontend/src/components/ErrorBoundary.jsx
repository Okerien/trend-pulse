import { Component } from "react";

// Stops one bad render from white-screening the whole app.
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }
  static getDerivedStateFromError(error) {
    return { error };
  }
  componentDidCatch(error, info) {
    console.error("Trend Pulse error:", error, info);
  }
  render() {
    if (this.state.error) {
      return (
        <div className="error-screen">
          <div className="error-card">
            <h2>Something went wrong</h2>
            <p>An unexpected error occurred. Reloading usually fixes it.</p>
            <button className="ghost-btn accent" onClick={() => window.location.reload()}>Reload</button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
