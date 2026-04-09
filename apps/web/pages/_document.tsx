import Document, { Html, Head, Main, NextScript, DocumentContext } from "next/document";

import { PRODUCT_META_DESCRIPTION } from "../lib/branding";

export default class MyDocument extends Document {
  static async getInitialProps(ctx: DocumentContext) {
    const initialProps = await Document.getInitialProps(ctx);
    return initialProps;
  }

  render() {
    return (
      <Html lang="en">
        <Head>
          <meta charSet="utf-8" />
          <meta name="description" content={PRODUCT_META_DESCRIPTION} />
          <meta name="theme-color" content="#fcfbf7" />
        </Head>
        <body>
          <Main />
          <NextScript />
        </body>
      </Html>
    );
  }
}
