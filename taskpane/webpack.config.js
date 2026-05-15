const path = require("path");
const HtmlWebpackPlugin = require("html-webpack-plugin");

const devCerts = (() => {
  try {
    return require("office-addin-dev-certs");
  } catch {
    return null;
  }
})();

module.exports = async (env, options) => {
  const isDev = options.mode !== "production";
  const https = isDev && devCerts
    ? await devCerts.getHttpsServerOptions()
    : true;

  return {
    entry: "./src/index.tsx",
    output: {
      path: path.resolve(__dirname, "dist"),
      filename: "taskpane.js",
      clean: true,
    },
    resolve: { extensions: [".ts", ".tsx", ".js"] },
    module: {
      rules: [
        { test: /\.tsx?$/, use: "ts-loader", exclude: /node_modules/ },
        { test: /\.css$/, use: ["style-loader", "css-loader"] },
      ],
    },
    plugins: [
      new HtmlWebpackPlugin({
        template: "./src/index.html",
        filename: "taskpane.html",
      }),
    ],
    devServer: {
      port: 3000,
      https,
      headers: { "Access-Control-Allow-Origin": "*" },
    },
    devtool: isDev ? "source-map" : false,
  };
};
