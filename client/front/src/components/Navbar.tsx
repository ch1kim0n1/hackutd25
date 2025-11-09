import { Navbar as HeroNavbar, NavbarBrand, NavbarContent, NavbarItem } from "@heroui/navbar";
import { Chip } from "@heroui/chip";
import logoImage from "@/config/logo.webp";

interface NavbarProps {
  balance?: number;
  totalAssets?: number;
  portfolioChange?: number;
}

export const Navbar: React.FC<NavbarProps> = ({ 
  balance = 0, 
  totalAssets = 0,
  portfolioChange = 0 
}) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatChange = (change: number) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  return (
    <HeroNavbar 
      maxWidth="full" 
      className="bg-background border-b border-divider py-1.5"
      height="4rem"
    >
      {/* Logo Section */}
      <NavbarBrand>
        <div className="flex items-center gap-2">
          <img 
            src={logoImage} 
            alt="Apex Logo" 
            className="w-16 h-16 object-contain"
          />
          <p className="font-bold text-3xl text-foreground">Apex</p>
        </div>
      </NavbarBrand>

      {/* Balance and Assets Info Section */}
      <NavbarContent justify="end" className="gap-6">
        {/* Total Assets */}
        <NavbarItem className="hidden sm:flex flex-col items-end">
        </NavbarItem>

        {/* Portfolio Change */}
        <NavbarItem className="hidden md:flex">
        </NavbarItem>

        {/* Balance */}
        <NavbarItem>
        </NavbarItem>
      </NavbarContent>
    </HeroNavbar>
  );
};
