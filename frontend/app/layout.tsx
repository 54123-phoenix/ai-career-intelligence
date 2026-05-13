import type { Metadata } from 'next';
import './globals.css';
import { LanguageProvider } from '@/components/ui/LanguageProvider';
import { Navbar } from '@/components/layout/Navbar';

export const metadata: Metadata = {
  title: 'AI Career Intelligence — 智能职业决策平台',
  description: 'AI-powered career profiling, job recommendations, strategy generation, and path simulation.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="min-h-screen bg-white text-gray-900 antialiased">
        <LanguageProvider>
          <Navbar />
          {children}
        </LanguageProvider>
      </body>
    </html>
  );
}
