package com.wakatime

import java.io.*
import alpha.time.Some
import bravo.charlie.something.Other

<#assign licenseFirst = "/*">
<#assign licensePrefix = " * ">
<#assign licenseLast = " */">
<#include "${project.licensePath}">
<#if package?? && package != "">
package ${package}
</#if>

import delta.io.*
import echo.Foxtrot as Golf
import h

class MainActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
    }
}
