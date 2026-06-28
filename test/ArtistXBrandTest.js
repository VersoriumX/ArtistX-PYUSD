const PYUSD = artifacts.require('PYUSDImplementation');

contract('PYUSDImplementation XEN AGI Intent', function (accounts) {
    const [owner, user1, user2, recipient] = accounts;
    let token;

    beforeEach(async function () {
        token = await PYUSD.new({from: owner});
        await token.unpause({from: owner});
        // Mint some tokens for testing
        await token.increaseSupply(1000000, {from: owner});
        await token.transfer(user1, 100000, {from: owner});
    });

    it('should have correct metadata', async function () {
        assert.equal(await token.name(), "Xen AGI");
        assert.equal(await token.symbol(), "XEN");
    });

    it('should return quantum beast status', async function () {
        const status = await token.getQuantumBeastStatus();
        assert.include(status, "Travis Jerome Goff");
    });

    it('should increment neural sequence on transfer', async function () {
        const initialSeq = await token.neuralSequence();
        await token.transfer(user2, 1000, {from: user1});
        const finalSeq = await token.neuralSequence();
        assert.equal(finalSeq.toNumber(), initialSeq.toNumber() + 1);
    });

    it('should apply 5% royalty on transfer when enabled', async function () {
        // royaltyPercentage is 500 by default

        const amount = 10000;
        const expectedRoyalty = 500;
        const expectedRecipientBalance = (await token.balanceOf(owner)).toNumber() + expectedRoyalty;

        await token.transfer(user2, amount, {from: user1});

        const recipientBalance = await token.balanceOf(owner);
        const receiverBalance = await token.balanceOf(user2);

        assert.equal(recipientBalance.toNumber(), expectedRecipientBalance);
        assert.equal(receiverBalance.toNumber(), amount - expectedRoyalty);
    });

    it('should allow owner to change royalty recipient', async function () {
        await token.setRoyaltyRecipient(recipient, {from: owner});
        await token.setRoyaltyPercentage(500, {from: owner});
        assert.equal(await token.royaltyRecipient(), recipient);

        await token.transfer(user2, 10000, {from: user1});
        const recipientBalance = await token.balanceOf(recipient);
        assert.equal(recipientBalance.toNumber(), 500);
    });

    it('should have the quantum sealed signature', async function () {
        const sig = await token.QUANTUM_SEALED_SIGNATURE();
        assert.equal(sig, "05adabd388eb612a990fc22ba3035fb3762d20a5dcc9cde5921eeb1029d749267259fbc320251374ad4a9b88e8445a60d4e9bdc154ec7fdfa217916c2981634b");
    });
});
