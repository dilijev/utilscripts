"use strict"

let albhed = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!@#$%^&*()'
let english = 'epstiwknuvgclrybxhmdofzqajEPSTIWKNUVGCLRYBXHMDOFZQAJ!@#$%^&*()1234567890'

function usage() {
    console.log(`
Specify either -a (to Al Bhed) or -e (To English) and the input text.
    $ node albhedtranslate.js -a "what is this"
    fryd ec drec
    $ node albhedtranslate.js -e "fryd ec drec"
`)
}

let argv = process.argv
let argc = argv.length

console.log(JSON.stringify([argc, argv]))

if (argc !== 4) {
    usage()
    return
}

let type = process.argv[2]
let input = process.argv[3]

let isToAlBhed = null
if (type === '-a') {
    isToAlBhed = true // english to al bhed
} else if (type === '-e') {
    isToAlBhed = false // al bhed to english
} else {
    usage()
    return
}

function translate(from, to, input) {
    let ret = ''
    for (let x of input) {
        let index = from.indexOf(x)
        if (index === -1) {
            ret += x;
        } else {
            let char = to[index]
            ret += char
        }
    }
    return ret
}

function e2ab(input) {
    return translate(english, albhed, input)
}

function ab2e(input) {
    return translate(albhed, english, input)
}

let out = ''

if (isToAlBhed) {
    out = e2ab(input)
} else {
    out = ab2e(input)
}

console.log(out)
