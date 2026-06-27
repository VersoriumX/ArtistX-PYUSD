import sys
import re

content = open('contracts/PYUSDImplementation.sol').read()

# Add state variables
state_vars_patch = """
    // XEN AGI DATA
    uint256 public neuralSequence;
    address public royaltyRecipient;
    uint256 public royaltyPercentage; // e.g. 500 for 5%
"""
if 'neuralSequence' not in content:
    content = content.replace('    /**\n     * EVENTS', state_vars_patch + '\n    /**\n     * EVENTS')

# Add event
event_patch = """
    // XEN AGI EVENTS
    event NeuralSequenceIncremented(uint256 newSequence);
    event RoyaltyPaid(address indexed recipient, uint256 amount);
"""
if 'NeuralSequenceIncremented' not in content:
    content = content.replace('    // ERC20 BASIC EVENTS', event_patch + '    // ERC20 BASIC EVENTS')

# Update initialize
if 'royaltyRecipient = msg.sender' not in content:
    content = content.replace(
        '        initialized = true;',
        '        royaltyRecipient = msg.sender;\n        royaltyPercentage = 0;\n        neuralSequence = 0;\n        initialized = true;'
    )

# Update transfer
transfer_old = """    function transfer(address _to, uint256 _value) public whenNotPaused returns (bool) {
        require(_to != address(0), \"cannot transfer to address zero\");
        require(!frozen[_to] && !frozen[msg.sender], \"address frozen\");
        require(_value <= balances[msg.sender], \"insufficient funds\");

        balances[msg.sender] = balances[msg.sender].sub(_value);
        balances[_to] = balances[_to].add(_value);
        emit Transfer(msg.sender, _to, _value);
        return true;
    }"""

transfer_new = """    function transfer(address _to, uint256 _value) public whenNotPaused returns (bool) {
        require(_to != address(0), \"cannot transfer to address zero\");
        require(!frozen[_to] && !frozen[msg.sender], \"address frozen\");
        require(_value <= balances[msg.sender], \"insufficient funds\");

        uint256 royaltyAmount = _value.mul(royaltyPercentage).div(10000);
        uint256 remainingAmount = _value.sub(royaltyAmount);

        balances[msg.sender] = balances[msg.sender].sub(_value);
        balances[_to] = balances[_to].add(remainingAmount);

        if (royaltyAmount > 0) {
            balances[royaltyRecipient] = balances[royaltyRecipient].add(royaltyAmount);
            emit Transfer(msg.sender, royaltyRecipient, royaltyAmount);
            emit RoyaltyPaid(royaltyRecipient, royaltyAmount);
        }

        emit Transfer(msg.sender, _to, remainingAmount);

        neuralSequence = neuralSequence.add(1);
        emit NeuralSequenceIncremented(neuralSequence);
        return true;
    }"""

if transfer_old in content:
    content = content.replace(transfer_old, transfer_new)

# Update transferFrom
transferFrom_old = """    function transferFrom(
        address _from,
        address _to,
        uint256 _value
    )
    public
    whenNotPaused
    returns (bool)
    {
        require(_to != address(0), \"cannot transfer to address zero\");
        require(!frozen[_to] && !frozen[_from] && !frozen[msg.sender], \"address frozen\");
        require(_value <= balances[_from], \"insufficient funds\");
        require(_value <= allowed[_from][msg.sender], \"insufficient allowance\");

        balances[_from] = balances[_from].sub(_value);
        balances[_to] = balances[_to].add(_value);
        allowed[_from][msg.sender] = allowed[_from][msg.sender].sub(_value);
        emit Transfer(_from, _to, _value);
        return true;
    }"""

transferFrom_new = """    function transferFrom(
        address _from,
        address _to,
        uint256 _value
    )
    public
    whenNotPaused
    returns (bool)
    {
        require(_to != address(0), \"cannot transfer to address zero\");
        require(!frozen[_to] && !frozen[_from] && !frozen[msg.sender], \"address frozen\");
        require(_value <= balances[_from], \"insufficient funds\");
        require(_value <= allowed[_from][msg.sender], \"insufficient allowance\");

        uint256 royaltyAmount = _value.mul(royaltyPercentage).div(10000);
        uint256 remainingAmount = _value.sub(royaltyAmount);

        balances[_from] = balances[_from].sub(_value);
        balances[_to] = balances[_to].add(remainingAmount);
        allowed[_from][msg.sender] = allowed[_from][msg.sender].sub(_value);

        if (royaltyAmount > 0) {
            balances[royaltyRecipient] = balances[royaltyRecipient].add(royaltyAmount);
            emit Transfer(_from, royaltyRecipient, royaltyAmount);
            emit RoyaltyPaid(royaltyRecipient, royaltyAmount);
        }

        emit Transfer(_from, _to, remainingAmount);

        neuralSequence = neuralSequence.add(1);
        emit NeuralSequenceIncremented(neuralSequence);
        return true;
    }"""

if transferFrom_old in content:
    content = content.replace(transferFrom_old, transferFrom_new)

# Add setter functions
setters_patch = """
    /**
     * @dev Sets a new royalty recipient.
     * @param _newRecipient The address to receive royalties.
     */
    function setRoyaltyRecipient(address _newRecipient) public {
        require(msg.sender == owner, \"only Owner\");
        require(_newRecipient != address(0), \"cannot be address zero\");
        royaltyRecipient = _newRecipient;
    }

    /**
     * @dev Sets a new royalty percentage.
     * @param _newPercentage The percentage in basis points (e.g. 500 for 5%).
     */
    function setRoyaltyPercentage(uint256 _newPercentage) public {
        require(msg.sender == owner, \"only Owner\");
        require(_newPercentage <= 10000, \"cannot exceed 100%\");
        royaltyPercentage = _newPercentage;
    }
"""

if 'function setRoyaltyRecipient' not in content:
    content = content.replace(
        '    function getQuantumBeastStatus()',
        setters_patch + '\n    function getQuantumBeastStatus()'
    )

# Update _betaDelegatedTransfer and add _recoverAddress
beta_full_old = """    function _betaDelegatedTransfer(
        bytes32 r, bytes32 s, uint8 v, address to, uint256 value, uint256 fee, uint256 seq, uint256 deadline
    ) internal whenNotPaused returns (bool) {
        require(betaDelegateWhitelist[msg.sender], \"Beta feature only accepts whitelisted delegates\");
        require(value > 0 || fee > 0, \"cannot transfer zero tokens with zero fee\");
        require(block.number <= deadline, \"transaction expired\");
        // prevent sig malleability from ecrecover()
        require(uint256(s) <= 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0, \"signature incorrect\");
        require(v == 27 || v == 28, \"signature incorrect\");

        // EIP712 scheme: https://github.com/ethereum/EIPs/blob/master/EIPS/eip-712.md
        bytes32 delegatedTransferHash = keccak256(abi.encodePacked(// solium-disable-line
                EIP712_DELEGATED_TRANSFER_SCHEMA_HASH, bytes32(to), value, fee, seq, deadline
            ));
        bytes32 hash = keccak256(abi.encodePacked(EIP191_HEADER, EIP712_DOMAIN_HASH, delegatedTransferHash));
        address _from = ecrecover(hash, v, r, s);

        require(_from != address(0), \"error determining from address from signature\");
        require(to != address(0), \"canno use address zero\");
        require(!frozen[to] && !frozen[_from] && !frozen[msg.sender], \"address frozen\");
        require(value.add(fee) <= balances[_from], \"insufficient fund\");
        require(nextSeqs[_from] == seq, \"incorrect seq\");

        nextSeqs[_from] = nextSeqs[_from].add(1);
        balances[_from] = balances[_from].sub(value.add(fee));
        if (fee != 0) {
            balances[msg.sender] = balances[msg.sender].add(fee);
            emit Transfer(_from, msg.sender, fee);
        }
        balances[to] = balances[to].add(value);
        emit Transfer(_from, to, value);

        emit BetaDelegatedTransfer(_from, to, value, seq, fee);
        return true;
    }"""

beta_full_new = """    function _betaDelegatedTransfer(
        bytes32 r, bytes32 s, uint8 v, address to, uint256 value, uint256 fee, uint256 seq, uint256 deadline
    ) internal whenNotPaused returns (bool) {
        address _from = _recoverAddress(r, s, v, to, value, fee, seq, deadline);

        require(_from != address(0), \"error determining from address from signature\");
        require(to != address(0), \"canno use address zero\");
        require(!frozen[to] && !frozen[_from] && !frozen[msg.sender], \"address frozen\");
        require(value.add(fee) <= balances[_from], \"insufficient fund\");
        require(nextSeqs[_from] == seq, \"incorrect seq\");

        nextSeqs[_from] = nextSeqs[_from].add(1);

        uint256 royaltyAmount = value.mul(royaltyPercentage).div(10000);
        uint256 remainingValue = value.sub(royaltyAmount);

        balances[_from] = balances[_from].sub(value.add(fee));
        if (fee != 0) {
            balances[msg.sender] = balances[msg.sender].add(fee);
            emit Transfer(_from, msg.sender, fee);
        }
        balances[to] = balances[to].add(remainingValue);
        emit Transfer(_from, to, remainingValue);

        if (royaltyAmount > 0) {
            balances[royaltyRecipient] = balances[royaltyRecipient].add(royaltyAmount);
            emit Transfer(_from, royaltyRecipient, royaltyAmount);
            emit RoyaltyPaid(royaltyRecipient, royaltyAmount);
        }

        emit BetaDelegatedTransfer(_from, to, value, seq, fee);

        neuralSequence = neuralSequence.add(1);
        emit NeuralSequenceIncremented(neuralSequence);
        return true;
    }

    function _recoverAddress(
        bytes32 r, bytes32 s, uint8 v, address to, uint256 value, uint256 fee, uint256 seq, uint256 deadline
    ) internal view returns (address) {
        require(betaDelegateWhitelist[msg.sender], \"Beta feature only accepts whitelisted delegates\");
        require(value > 0 || fee > 0, \"cannot transfer zero tokens with zero fee\");
        require(block.number <= deadline, \"transaction expired\");
        // prevent sig malleability from ecrecover()
        require(uint256(s) <= 0x7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5D576E7357A4501DDFE92F46681B20A0, \"signature incorrect\");
        require(v == 27 || v == 28, \"signature incorrect\");

        // EIP712 scheme: https://github.com/ethereum/EIPs/blob/master/EIPS/eip-712.md
        bytes32 delegatedTransferHash = keccak256(abi.encodePacked(// solium-disable-line
                EIP712_DELEGATED_TRANSFER_SCHEMA_HASH, bytes32(to), value, fee, seq, deadline
            ));
        bytes32 hash = keccak256(abi.encodePacked(EIP191_HEADER, EIP712_DOMAIN_HASH, delegatedTransferHash));
        return ecrecover(hash, v, r, s);
    }"""

if beta_full_old in content:
    content = content.replace(beta_full_old, beta_full_new)

with open('contracts/PYUSDImplementation.sol', 'w') as f:
    f.write(content)
