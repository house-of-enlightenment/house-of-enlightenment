const R = require("ramda");

module.exports = (data) => {

  const output = R.compose(
    R.map(obj => {
      return R.merge(obj, {
        point: R.map(R.multiply(200), obj.point)
      });
    })
  )(data);

  return output;
};
