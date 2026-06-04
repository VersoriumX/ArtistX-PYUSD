var HDWalletProvider = require("@truffle/hdwallet-provider");
const mnemonic = "<your-mnemonic>";
const walletChildNum = 0;
const networkAddressMainnet = "https://mainnet.infura.io/v3/<your-api-key>";
const networkAddressTestnet = "https://goerli.infura.io/v3/<your-api-key>";
const Web3 = require("web3");

module.exports = {
  plugins: ["solidity-coverage"],
  networks: {
    development: {
      provider: function() {
        return new Web3.providers.HttpProvider("http://127.0.0.1:8545")
      },
      network_id: '*',
      gas: 6700000,
      gasPrice: 0x01,
      disableConfirmationListener: true
    }
  },
  solc: {
    optimizer: {
      enabled: true,
      runs: 200
    }
  }
};
