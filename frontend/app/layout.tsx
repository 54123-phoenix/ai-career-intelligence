import type { Metadata } from 'next';
import './globals.css';
import { LanguageProvider } from '@/components/ui/LanguageProvider';

export const metadata: Metadata = {
  title: 'AI Career Intelligence — Strategic Career Decision System',
  description: 'Multi-Agent career simulation and strategy optimization platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" className="dark" suppressHydrationWarning>
      <body className="min-h-screen bg-slate-950 text-slate-100 antialiased">
        <LanguageProvider>{children}</LanguageProvider>
      </body>
    </html>
  );
}
