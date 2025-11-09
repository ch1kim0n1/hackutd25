import {
  Navbar as HeroNavbar,
  NavbarBrand,
  NavbarContent,
  NavbarItem,
} from "@heroui/navbar";
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
  portfolioChange = 0,
}) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "USD",
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatChange = (change: number) => {
    const sign = change >= 0 ? "+" : "";

    return `${sign}${change.toFixed(2)}%`;
  };

  return (
    <HeroNavbar
      className="bg-background border-b border-divider py-1.5"
      height="4rem"
      maxWidth="full"
    >
      {/* Logo Section */}
      <NavbarBrand>
        <div className="flex items-center gap-2">
          <img
            alt="Apex Logo"
            className="w-16 h-16 object-contain"
            src={logoImage}
          />
          <p className="font-bold text-3xl text-foreground">Apex</p>
        </div>
      </NavbarBrand>

      {/* Balance and Assets Info Section */}
      <NavbarContent className="gap-6" justify="end">
        {/* Total Assets */}
        <NavbarItem className="hidden sm:flex flex-col items-end">
          <span className="text-xs text-default-500">Total Assets</span>
          <span className="text-sm font-semibold text-foreground">
            {totalAssets}
          </span>
        </NavbarItem>

        {/* Portfolio Change */}
        <NavbarItem className="hidden md:flex">
          <Chip
            classNames={{
              base: "font-mono",
              content: "text-xs font-semibold",
            }}
            color={portfolioChange >= 0 ? "success" : "danger"}
            size="sm"
            variant="flat"
          >
            {formatChange(portfolioChange)}
          </Chip>
        </NavbarItem>

        {/* Balance */}
        <NavbarItem>
          <Chip
            classNames={{
              base: "px-4 py-2",
              content: "flex flex-col items-end gap-0",
            }}
            color="primary"
            size="lg"
            variant="flat"
          >
            <span className="text-xs text-default-500">Balance</span>
            <span className="text-lg font-bold font-mono">
              {formatCurrency(balance)}
            </span>
          </Chip>
        </NavbarItem>
      </NavbarContent>
    </HeroNavbar>
  );
};
