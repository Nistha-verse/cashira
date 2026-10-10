const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const factory = await hre.ethers.getContractFactory("CashiraAnchor");
  const contract = await factory.deploy(deployer.address);
  await contract.waitForDeployment();
  console.log(`CashiraAnchor deployed by ${deployer.address} at ${await contract.getAddress()}`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
