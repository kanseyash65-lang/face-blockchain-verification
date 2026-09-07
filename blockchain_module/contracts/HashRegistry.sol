// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

contract HashRegistry {
    struct Record {
        string dataHash;
        uint256 timestamp;
        address submitter;
    }

    Record[] public records;

    event RecordStored(uint256 indexed recordId, string dataHash, uint256 timestamp, address submitter);

    function storeHash(string memory dataHash) public {
        records.push(Record({
            dataHash: dataHash,
            timestamp: block.timestamp,
            submitter: msg.sender
        }));

        emit RecordStored(records.length - 1, dataHash, block.timestamp, msg.sender);
    }

    function getRecord(uint256 recordId) public view returns (string memory, uint256, address) {
        Record memory record = records[recordId];
        return (record.dataHash, record.timestamp, record.submitter);
    }

    function getRecordCount() public view returns (uint256) {
        return records.length;
    }
}