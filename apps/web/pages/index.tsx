import type { NextPage } from "next";

const Home: NextPage = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      <main className="container mx-auto px-4 py-20">
        <div className="max-w-2xl mx-auto text-center">
          <h1 className="text-5xl font-bold mb-6">
            Real-Time Content Ranking System
          </h1>
          <p className="text-xl text-slate-300 mb-12">
            A distributed event-driven platform for personalized content ranking.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
            <div className="bg-slate-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">🎯 Feed</h3>
              <p className="text-slate-300">Personalized content feed</p>
            </div>
            <div className="bg-slate-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">📊 Analytics</h3>
              <p className="text-slate-300">Real-time metrics & dashboards</p>
            </div>
            <div className="bg-slate-700 rounded-lg p-6">
              <h3 className="text-lg font-semibold mb-2">⚡ Performance</h3>
              <p className="text-slate-300">Low-latency ranking engine</p>
            </div>
          </div>

          <div className="bg-slate-700 rounded-lg p-8 text-left">
            <h2 className="text-2xl font-bold mb-4">Tech Stack</h2>
            <ul className="space-y-2 text-slate-300">
              <li>✓ FastAPI + Python backend services</li>
              <li>✓ Apache Kafka for event streaming</li>
              <li>✓ PostgreSQL + Redis</li>
              <li>✓ Prometheus + Grafana monitoring</li>
              <li>✓ Docker Compose for local development</li>
            </ul>
          </div>

          <div className="mt-12">
            <p className="text-slate-400">
              🚀 Phase 0: Foundation and setup in progress
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Home;
