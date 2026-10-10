// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

/// @notice Stores only a loan reference and signed audit hash for illustration.
contract CashiraAnchor is Ownable {
    struct Anchor {
        string loanRef;
        bytes32 recordHash;
        string ruleVersion;
        uint256 timestamp;
    }

    mapping(bytes32 => Anchor) public anchors;

    event RecordAnchored(
        string loanRef,
        bytes32 indexed recordHash,
        string ruleVersion,
        uint256 timestamp
    );

    constructor(address initialOwner) Ownable(initialOwner) {}

    function anchor(
        string calldata loanRef,
        bytes32 recordHash,
        string calldata ruleVersion
    ) external onlyOwner {
        uint256 timestamp = block.timestamp;
        anchors[recordHash] = Anchor(loanRef, recordHash, ruleVersion, timestamp);
        emit RecordAnchored(loanRef, recordHash, ruleVersion, timestamp);
    }
}
