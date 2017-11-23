// Hello.java
import java.io.*;
import static java.lang.Math.*;
import static com.googlecode.javacv.jna.highgui.cvReleaseCapture;
import javax.servlet.*;
import com.colorfulwolf.webcamapplet.gui.ImagePanel;
import com.foobar.*;
import package com.apackage.something;
import namespace com.anamespace.other;

public class Hello extends GenericServlet {
    public void service(final ServletRequest request, final ServletResponse response)
    throws ServletException, IOException {
        response.setContentType("text/html");
        final PrintWriter pw = response.getWriter();
        try {
            pw.println("Hello, world!");
        } finally {
            pw.close();
        }
    }
}
