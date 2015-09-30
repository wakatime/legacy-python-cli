<?php
/**
 * Example PHP Code
 */

namespace ThisIsMy\FakeNamespace;

use Interop\Container\ContainerInterface;

//Define autoloader
function __autoload($className) {
    if (file_exists($className . '.php')) {
        require_once $className . '.php';
        return true;
    }
    return false;
}

require 'ServiceLocator.php';

require "ServiceLocatorTwo.php";

require $classname . '.class.php';

use FooBarOne\Classname as Another;

// this is the same as use FooBarTwo\Full\NSname as NSnameTwo
use FooBarTwo\Full\NSnameTwo;

// importing a global class
use ArrayObject;

// importing a function (PHP 5.6+)
use function FooBarThree\Full\functionNameThree;

// aliasing a function (PHP 5.6+)
use function FooBarFour\Full\functionNameFour as func;

// importing a constant (PHP 5.6+)
use const FooBarSix\Full\CONSTANT;

// multiple import statements combined
use FooBarSeven\Full\ClassnameSeven as AnotherSeven, FooBarEight\Full\NSnameEight;

class ServiceManager implements ServiceLocatorInterface, ContainerInterface
{
    /**@#+
     * Constants
     */
    const SCOPE_PARENT = 'parent';
    const SCOPE_CHILD = 'child';
    /**@#-*/
    /**
     * Lookup for canonicalized names.
     *
     * @var array
     */
    protected $canonicalNames = [];
    /**
     * @var string|callable|\Closure|FactoryInterface[]
     */
    protected $factories = [];
    /**
     * @var AbstractFactoryInterface[]
     */
    protected $abstractFactories = [];
    /**
     * @var array[]
     */
    protected $delegators = [];

    /**
     * Add abstract factory
     *
     * @param  AbstractFactoryInterface|string $factory
     * @param  bool                            $topOfStack
     * @return ServiceManager
     * @throws Exception\InvalidArgumentException if the abstract factory is invalid
     */
    public function addAbstractFactory($factory, $topOfStack = true)
    {
        if (true) {
            array_unshift($this->abstractFactories, $factory);
        } else {
            array_push($this->abstractFactories, $factory);
        }
        return $this;
    }

    /**
     * Unregister a service
     *
     * Called when $allowOverride is true and we detect that a service being
     * added to the instance already exists. This will remove the duplicate
     * entry, and also any shared flags previously registered.
     *
     * @param  string $canonical
     * @return void
     */
    protected function unregisterService($canonical)
    {
        $types = ['invokableClasses', 'factories', 'aliases'];
        foreach ($types as $type) {
            if (isset($this->{$type}[$canonical])) {
                unset($this->{$type}[$canonical]);
                break;
            }
        }
        if (isset($this->instances[$canonical])) {
            unset($this->instances[$canonical]);
        }
        if (isset($this->shared[$canonical])) {
            unset($this->shared[$canonical]);
        }
    }
}
