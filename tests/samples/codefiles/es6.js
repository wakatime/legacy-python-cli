import Alpha from './bravo';
import { charlie, delta } from '../../echo/foxtrot';
import golf from './hotel/india.js';
import juliett from 'kilo';
import {
  lima,
  mike,
} from './november';
import * from '/modules/oscar';
import * as papa from 'quebec';
import {romeo as sierra} from from 'tango.jsx';
import 'uniform.js';
import victorDefault, * as victorModule from '/modules/victor.js';
import whiskeyDefault, {whiskeyOne, whiskeyTwo} from 'whiskey';

const propTypes = {};

const defaultProps = {};

class Link extends Alpha.Component {
  static method() {
    return true;
  }

  render() {
    return (
      <a href={this.props.url} data-id={this.props.id}>
        {this.props.text}
      </a>
    );
  }
}

Link.propTypes = propTypes;
Link.defaultProps = defaultProps;

export default Link;
