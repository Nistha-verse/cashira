const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("CashiraAnchor", function () {
  async function deployed() {
    const [owner, other] = await ethers.getSigners();
    const factory = await ethers.getContractFactory("CashiraAnchor");
    const contract = await factory.deploy(owner.address);
    await contract.waitForDeployment();
    return { contract, owner, other };
  }

  it("allows the owner to anchor and emits an event", async function () {
    const { contract } = await deployed();
    const hash = ethers.keccak256(ethers.toUtf8Bytes("record"));
    await expect(contract.anchor("1", hash, "cashira-emi-v1"))
      .to.emit(contract, "RecordAnchored")
      .withArgs("1", hash, "cashira-emi-v1", (value) => value > 0);
    const stored = await contract.anchors(hash);
    expect(stored.loanRef).to.equal("1");
    expect(stored.recordHash).to.equal(hash);
    expect(stored.ruleVersion).to.equal("cashira-emi-v1");
  });

  it("rejects unauthorized writers", async function () {
    const { contract, other } = await deployed();
    const hash = ethers.keccak256(ethers.toUtf8Bytes("record"));
    await expect(contract.connect(other).anchor("1", hash, "cashira-emi-v1"))
      .to.be.revertedWithCustomError(contract, "OwnableUnauthorizedAccount")
      .withArgs(other.address);
  });
});
