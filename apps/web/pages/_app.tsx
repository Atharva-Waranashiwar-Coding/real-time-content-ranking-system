import "../styles/globals.css";
import type { AppProps } from "next/app";

import { DemoProvider } from "../lib/demo-context";

function MyApp({ Component, pageProps }: AppProps) {
  return (
    <DemoProvider>
      <Component {...pageProps} />
    </DemoProvider>
  );
}

export default MyApp;
