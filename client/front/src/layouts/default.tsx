import { Navbar } from "@/components/Navbar";

export default function DefaultLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  // Mock data - in real app this would come from state management
  const balance = 125430.67;
  const totalAssets = 10;
  const portfolioChange = 2.34;

  return (
    <div className="relative flex flex-col h-screen">
      <Navbar
        balance={balance}
        portfolioChange={portfolioChange}
        totalAssets={totalAssets}
      />
      <main className="bg-background flex-grow overflow-y-auto">
        {children}
      </main>
    </div>
  );
}
