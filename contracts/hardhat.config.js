require("dotenv").config();
require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.24",
  networks: {
    hardhat: {},
    polygonAmoy: {
      url: process.env.POLYGON_AMOY_RPC_URL || "",
      accounts: process.env.CHAIN_PRIVATE_KEY ? [process.env.CHAIN_PRIVATE_KEY] : [],
      chainId: 80002,
    },
  },
};
