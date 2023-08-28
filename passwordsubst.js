"use strict";

// substitute password symbols with randomly generated characters in the same class
// convert uppercase letters to random uppercase letters
// convert lowercase letters to random lowercase letters
// convert numbers to random numbers
// convert symbols to random symbols in the set `~!@#$%^&*()_+-={}[]:";'<>,.?/\|`
function convert(password) {
    // return pseudo-password
    password = password.replace(/[a-z]/g, random_lowercase);
    password = password.replace(/[A-Z]/g, random_uppercase);
    password = password.replace(/[0-9]/g, random_number);
    password = password.replace(/[~!@#$%^&*()_+\-={}\[\]:";'<>,.?\/\\|]/g, random_symbol);
    return password;
}

// return a random lowercase letter
function random_lowercase() {
    return String.fromCharCode(Math.floor(Math.random() * 26) + 0x61);
}

// return a random uppercase letter
function random_uppercase() {
    return String.fromCharCode(Math.floor(Math.random() * 26) + 0x41);
}

// return a random number
function random_number() {
    return String.fromCharCode(Math.floor(Math.random() * 10) + 0x30);
}

// return a random symbol
function random_symbol() {
    const symbols_list = '~!@#$%^&*()_+-={}[]:";\'<>,.?/\\|';
    const symbols_list_length = symbols_list.length;
    return "" + symbols_list[Math.floor(Math.random() * symbols_list_length)];
}

// node main function
function main() {
    // read password from args
    let argv = process.argv;
    let argc = argv.length;

    console.log([argv, argc]);

    if (argc < 3) {
        console.log('Usage: node passwordsubst.js <password>');
        return;
    }

    // convert password
    let password = argv[2];
    let converted_password = convert(password);
    console.log(converted_password);
}

main();
