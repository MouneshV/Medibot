'use client';

import './globals.css';

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>MediBot - Medical Assistant</title>
      </head>
      <body>
        <div id="root">{children}</div>
      </body>
    </html>
  );
}
