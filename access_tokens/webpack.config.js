const path = require('path');
const CopyPlugin = require('copy-webpack-plugin');

module.exports = {
    mode: 'development',
    entry: './static/js/index.js',
    output: {
        filename: 'main.js',
        path: path.resolve(__dirname, 'static/dist'),
    },
    devServer: {
        static: {
            directory: path.join(__dirname, 'static'),
        },
        port: 8080,
    },
    plugins: [
        new CopyPlugin({
            patterns: [
                { from: './static/index.html', to: '' }
            ],
        }),
    ],
};
