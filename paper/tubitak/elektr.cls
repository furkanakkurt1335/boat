%%% STYLE of the Turkish Journal of Elektr.
%%% Author: Abdullah Can
%%% Revision : 1.0
%%% ====================================================================
%%%  @LaTeX-file{
%%%     filename        = "elektr.cls"
%%%     author          = "Abdullah Can"
%%%     address         = "Abdullah Can
%%%                        Bas Teknisyen
%%%                        Kavaklidere Ankara/Turkey"
%%%     telephone       = "(+90) 312-298 96 12"
%%%     email           = "abdullah.can@tubitak.gov.tr"
%%%     keywords        = "elektr.cls"
%%%  }
%%% ====================================================================


\if@compatibility
\input{amsart.sty}
\else
\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{elektr}[1998/04/17 v1.0 TUBITAK - Turkish Journal of 
Elektrik]
\newif\if@draftcopy
\@draftcopyfalse
\DeclareOption{a5paper}
    {\ClassError{Elektrik}{Option `a5paper' not supported}{}}
\DeclareOption{b5paper}
    {\ClassError{Elektrik}{Option `b5paper' not supported}{}}
\DeclareOption{twocolumn}%
    {\ClassError{Elektrik}{Option `twocolumn' not supported}{}}
\DeclareOption{titlepage}%
    {\ClassError{Elektrik}{Option `titlepage' not supported}{}}
\DeclareOption{draft}
    {\@draftcopytrue
    \setlength\overfullrule{5pt}}
\DeclareOption{final}
    {\@draftcopyfalse
     \setlength\overfullrule{0pt}}
     
\PassOptionsToClass{letterpaper,twoside}{article}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ProcessOptions
\LoadClass{article}
\ExecuteOptions{letterpaper,10pt,onecolumn,final}
%%%%%%%%%%%%%%%%% CAPTION %%%%%%%%%%%%%%%%%%%%%%


\setlength\abovecaptionskip{10\p@}
\setlength\belowcaptionskip{0\p@}

\long\def\@makecaption#1#2{%
  \vskip\abovecaptionskip
  \sbox\@tempboxa{\small{\bfseries #1}. #2}%
  \ifdim \wd\@tempboxa >\hsize
    {\small {\bfseries #1}. #2\par}
  \else
    \global \@minipagefalse
    \hb@xt@\hsize{\hfil\box\@tempboxa\hfil}%
  \fi
  \vskip\belowcaptionskip}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

%%%%%%%%%%%%%%%% PAGE SIZE DEFINITIONS %%%%%%%%%%%%%%%%

\tolerance=300
\pretolerance=200
\hfuzz=1 true pt
\vfuzz=1 true pt
\parindent=1 true cm
\mathsurround=1 true pt
\parskip=1pt plus .25pt minus .25pt
\normallineskiplimit=.99pt
\hoffset=-0.25cm      %sonradan eklendi.
\voffset=-1.25cm
%\hoffset=-0.1in       %sonradan eklendi.
%\voffset=-0.4in
%\topskip 20truept
\hsize=17 true cm
\vsize=22 true cm
\textwidth=17 true cm
\textheight=22 true cm
\oddsidemargin 0cm
\evensidemargin 0cm
\baselineskip=16pt
\lineskiplimit=4.5pt
\lineskip=5.5pt


\newfont{\abdullah}{cmr9 scaled \magstep0}
\newfont{\abdullahl}{cmr10 scaled \magstep0}
\def\ozbaslik #1{\gdef\@ozbaslik{#1}}
\def\soyad #1{\gdef\@soyad{#1}}
\def\fpage #1{\gdef\@fpage{#1}}
\def\lpage #1{\gdef\@lpage{#1}}
\def\ilksayfa #1{\gdef\@ilksayfa{#1}}
\def\sonsayfa #1{\gdef\@sonsayfa{#1}}
\def\vol #1{\gdef\@vol{#1}}
\def\yil #1{\gdef\@yil{#1}}
\def\doi #1{\gdef\@doi{#1}}
\def\rec #1{\gdef\@rec{#1}}
\def\acc #1{\gdef\@acc{#1}}
\def\finv #1{\gdef\@prin{#1}}
\def\orc #1{\gdef\@orc{#1}}


\renewcommand{\author}[2][]{
   \gdef\@surnames{#1/Turk J Elec Eng {\&} Comp Sci}\gdef\@author{#2}
   \ifx\@empty\@surnames \gdef\@surnames{Turk J Elec Eng {\&} Comp Sci}\fi
}



\def\@oddhead{\normalfont\hfil\small\@surnames\hfil}
\def\@oddfoot{\normalfont\hfil\thepage }
\def\@evenhead{\normalfont\hfil\small\@surnames\hfil}
\def\@evenfoot{\normalfont\thepage\hfil}

\renewcommand\maketitle{\par
  \begingroup
    \renewcommand\thefootnote{\@fnsymbol\c@footnote}%
    \def\@makefnmark{\rlap{\@textsuperscript{\normalfont\@thefnmark}}}%
    \long\def\@makefntext##1{\parindent 1em\noindent
            \hb@xt@0.5em{%
                \hss\@textsuperscript{\normalfont\@thefnmark}}{Correspondence:\ }
		    ##1
		    \vspace{-10mm}
		    \begin{center}
		 \raisebox{-15ex}[0ex][0ex]{ ~~ \raisebox{.5ex}[0ex][0ex]{This work is licensed under a Creative Commons Attribution 4.0 International License.}}
 		    \end{center} }%
      \newpage
      \global\@topnum\z@   % Prevents figures from going at top of page.
      \@maketitle
    \thispagestyle{myheadings}\@thanks
  \endgroup
  \setcounter{footnote}{0}%
  \global\let\thanks\relax
  \global\let\maketitle\relax
  \global\let\@maketitle\relax
  \global\let\@thanks\@empty
  \global\let\@author\@empty
  \global\let\@date\@empty
  \global\let\@title\@empty
  \global\let\title\relax
  \global\let\author\relax
  \global\let\date\relax
  \global\let\and\relax
}



\def\ps@myheadings{\let\@mkboth\@gobbletwo
\def\@oddhead{\makebox[\textwidth][l]{\abdullah Turk J Elec Eng {\&} Comp Sci,
\@yil, \@vol, %No.\@no,
\copyright T\"{U}B\.{I}TAK\hfill }}
\def\@oddfoot{\rm  \hfil \thepage }
\def\@evenhead{\makebox[\textwidth][l]{\abdullah Turk J Elec Eng {\&} Comp Sci,
\@yil. \@vol, %No.\@no, 
\copyright T\"{U}B\.{I}TAK\hfill }}
\def\@evenfoot{\rm \thepage \hfil}}


\def\ps@myheadings{%
    \def\@oddhead{\vbox{\serieslogo@}\hss}
    \def\@oddfoot{\normalfont  \hfil \thepage}
    \let\@evenhead\@oddhead
    \def\@evenfoot{\normalfont \thepage \hfil}
    \let\@mkboth\@gobbletwo
    \let\sectionmark\@gobble
    \let\subsectionmark\@gobble
}



\gdef\@soyad{}
\gdef\@vol{}
\gdef\@fpage{}
\gdef\@lpage{}
\gdef\@yil{}
\gdef\@rec{}
\gdef\@acc{}
\gdef\@finv{}
\gdef\@orc{}


\def\serieslogo@{\vtop to 5pt{%
  \parindent\z@ \small\normalfont
   \vskip .61cm%
  \hbox{\hspace*{12.6cm}\begin{tabular}{l}
  Turk J Elec Eng {\&} Comp Sci \\ [.6ex]
  (\@yil)\ \@vol:\ \@fpage\ -- \@lpage \\ [.6ex]  
  \copyright\ T\"{U}B\.{I}TAK\\ [.6ex]
   \@doi
  \end{tabular}\hfil}
  \hbox{\vspace*{-25.3mm}\hfill}
  \hbox{\hfill}
   \endgraf\vss}}

\def\@maketitle{%
  \newpage
  \null
  \vskip 6em%
  \begin{center}%
  \let \footnote \thanks
    {\large\bfseries \@title \par}%
    \vskip 1.5em%
    \lineskip .5em%
    {\small\begin{tabular}[t]{c}%
     \@author   \\ [-1.4em]  \hline \\ [-.8em] \\  \hline 
    \end{tabular}}
   {\@rec \@acc \@finv}
\\ [-1.4em]
    \vskip 1.5em%
  \end{center}%
}


\renewcommand{\orc}{\textcolor{orcidlogocol}{\aiOrcid}}

\renewcommand{\rec}[1]{\footnotesize{\bf Received:} #1 ~~~~~~~~\ \ \textbullet ~~~~~~~~}
\renewcommand{\acc}[1]{\footnotesize{\bf Accepted/Published Online:} #1 ~~~~~~~~\ \ \textbullet ~~~~~~~~}
\renewcommand{\finv}[1]{\footnotesize{\bf Final Version:} #1}

\RequirePackage[numbers,sort&compress]{natbib}

\renewenvironment{thebibliography}[1]
     {\zsection*{\refname
        \@mkboth{\MakeUppercase\refname}{\MakeUppercase\refname}}%
      \list{\@biblabel{\@arabic\c@enumiv}}%
           {\settowidth\labelwidth{\@biblabel{#1}}%
            \leftmargin\labelwidth
            \advance\leftmargin\labelsep
            \@openbib@code
            \usecounter{enumiv}%
            \let\p@enumiv\@empty
            \renewcommand\theenumiv{\@arabic\c@enumiv}}%
      \sloppy
      \small \vskip .3cm \parskip=-0.1pt \lineskip 4pt
      \clubpenalty4000
      \@clubpenalty \clubpenalty
      \widowpenalty4000%
      \sfcode`\.\@m}
     {\def\@noitemerr
       {\@latex@warning{Empty `thebibliography' environment}}%
      \endlist}


\newenvironment{reference}{\vskip .5cm\begin{thebibliography}{99}}
                        {\end{thebibliography}}



\renewenvironment{abstract}{%
\vskip 1em \small 
\noindent     {\bfseries \abstractname \vspace{\z@}:$\mbox{\!}$} 
}
   {\endquotation}

\newbox{\tempbox}
\newlength{\tcaplen}
\newlength{\ttcaplen}
\newcommand{\tablo}[2]{
    \par\vspace{10pt}\sbox{\tempbox}{\small{\textbf #1} #2}
    \ifdim \wd\tempbox > \linewidth
       \settowidth\tcaplen{\small\textbf #1\ }
        \setlength\ttcaplen\linewidth
        \addtolength{\ttcaplen}{-\tcaplen}
        {\noindent\small\mbox{{\bf #1\ }}\parbox[t]{\ttcaplen}{#2}}
    \else
    {\centerline{\small{\bf #1\ } #2}}
    \fi
}



\def\proof{\ifdim\lastskip <\bigskipamount\removelastskip\fi
             \vskip -\parskip
             \vskip\smallskipamount\vskip 0.2cm \noindent \rm{\bf Proof } }
\def\endproof{\smallskip\nopagebreak\hfill$\Box$\vskip -\parskip}

\newcommand\zsection{\@startsection {section}{1}{\z@}%
                      {-3.5ex \@plus -1ex \@minus -.2ex}%
                      {.5ex \@plus.2ex}%
                      {\centering\normalfont\bfseries}}%\normalsize
\renewcommand\section{\@startsection {section}{1}{\z@}%
                                   {-3.5ex \@plus -1ex \@minus -.2ex}%
                                   {.5ex \@plus.2ex}%
                                   {\normalfont\bfseries}}%\normalsize
\renewcommand\subsection{\@startsection{subsection}{2}{\z@}%
                                     {-3.25ex\@plus -1ex \@minus -.2ex}%
                                     {.5ex \@plus .2ex}%
                                     {\normalfont\bfseries}}%\normalsize
\renewcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}%
                                     {-3.25ex\@plus -1ex \@minus -.2ex}%
                                     {.5ex \@plus .2ex}%
                                     {\normalfont\bfseries}}%\normalsize

\renewcommand\@seccntformat[1]{\csname the#1\endcsname.~}

 \if@draftcopy\renewcommand\baselinestretch{2}\else
  \renewcommand\baselinestretch{}\fi
  
  \newcommand{\keywords}[1]{\par\vskip 0.2cm \noindent
{\bf Key words:} #1}

\endinput
%%
%% End of file `Elektrik.cls'.
