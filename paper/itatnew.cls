%% Based on easychair.cls by Serguei A. Mokhov, Andrei Voronkov,
%% and Geoff Sutcliffe (C) 2008
%% Modified for ITAT by
%% Tomas Vinar (C) 2013

\NeedsTeXFormat{LaTeX2e}[1995/12/01]
\ProvidesClass{itatnew}[2013/03/15]
%
\let\if@slovak\iffalse
\let\if@czech\iffalse
\DeclareOption{slovensky}{\let\if@slovak\iftrue}
\DeclareOption{cesky}{\let\if@czech\iftrue}
\ProcessOptions

% Running heads definitions

\def\titlerunning#1{\gdef\@titleRunning{#1}}
\def\authorrunning#1{\gdef\@authorRunning{#1}}
\titlerunning{easychair: Running title head is undefined.}
\authorrunning{easychair: Running author head is undefined.}

% We are an article (more customized later)
\LoadClass[a4paper,twocolumn,twoside]{article}
\RequirePackage[utf8x]{inputenc}
\if@slovak
  \RequirePackage[slovak]{babel}
\fi
\if@czech
  \RequirePackage[czech]{babel}
\fi
\RequirePackage[T1]{fontenc}
\RequirePackage{url}
\RequirePackage{hyperref}
\RequirePackage{graphicx}
\RequirePackage{mathptmx}
\RequirePackage{listings}
\RequirePackage{latexsym}
\RequirePackage{amsthm}

\setlength{\textheight}{24cm}
\setlength{\topmargin}{-0.85cm}
\setlength{\headheight}{0.5cm}
\setlength{\headsep}{0.65cm}
\setlength{\footskip}{1.25cm}
\flushbottom
\setlength{\hoffset}{-0.54cm}
\setlength{\textwidth}{17cm}
\setlength{\oddsidemargin}{0cm}
\setlength{\evensidemargin}{0cm}
\setlength{\marginparsep}{0cm}
\setlength{\marginparwidth}{0pt}
\setlength{\columnsep}{0.7cm}
\setlength{\parindent}{1em}




\RequirePackage{lastpage}
% To ensure the footnotes are always at the bottom
\RequirePackage[bottom]{footmisc}


%
% Allow for more space to place floats.
%
\renewcommand{\topfraction}{0.95}
\renewcommand{\bottomfraction}{0.95}
\renewcommand{\textfraction}{0.05}
\renewcommand{\floatpagefraction}{0.8}

\pagestyle{empty}
\date{}


% LNCS-like institute handling
\newcounter{@inst}
\def\inst#1{\unskip$^{#1}$}
\def\institute#1{\gdef\@institute{#1}}

\def\institutename{\par
 \begingroup
 \parskip=\z@
 \parindent=\z@
 \setcounter{@inst}{1}%
 \def\and{\par\stepcounter{@inst}%
 \noindent$^{\the@inst}$\enspace\ignorespaces}%
 \setbox0=\vbox{\def\thanks##1{}\@institute}%
 \ifnum\c@@inst=1\relax
   \gdef\fnnstart{0}%
 \else
   \xdef\fnnstart{\c@@inst}%
   \setcounter{@inst}{1}%
   \noindent$^{\the@inst}$\enspace
 \fi
 \ignorespaces
 \@institute\par
 \endgroup}


% Facelift a bit the title
\let\oldmaketitle=\maketitle
\def\@maketitle{%
	\newpage
	\null
	\vspace{-1cm}
	\begin{center}%
		\let \footnote \thanks
		{\LARGE{\@title}\par}
		\vskip 0.5\baselineskip
		\begin{tabular}[t]{c}%
		\@author
		\end{tabular}\par
                \vskip 0.5\baselineskip
                {\small\institutename}
	\end{center}%
	\par
	%\vskip \baselineskip
}


% Tighten up bibliography
\let\oldthebibliography=\thebibliography
\let\endoldthebibliography=\endthebibliography
\renewenvironment{thebibliography}[1]
{
	\small
	\begin{oldthebibliography}{#1}
		\setlength{\parskip}{2pt}
		\setlength{\itemsep}{0pt}
}
{
  \end{oldthebibliography}
}

% Language mutations
\def\supervisorname{Supervisor}
\def\keywordsname{Keywords}
\def\abstractname{Abstract}
\def\refname{References}

\def\theoremname{Theorem}
\def\casename{Case}
\def\conjecturename{Conjecture}
\def\corollaryname{Corollary}
\def\definitionname{Definition}
\def\examplename{Example}
\def\exercisename{Exercise}
\def\lemmaname{Lemma}
\def\notename{Note}
\def\problemname{Problem}
\def\propertyname{Property}
\def\questionname{Question}
\def\solutionname{Solution}
\def\lastandname{\unskip, and}

\if@slovak
  \def\supervisorname{Školiteľ}
  \def\keywordsname{Kľúčové slová}
  \def\abstractname{Abstrakt}
  \def\refname{Literatúra}

  \def\theoremname{Veta}
  \def\casename{Prípad}
  \def\conjecturename{Hypotéza}
  \def\corollaryname{Dôsledok}
  \def\definitionname{Definícia}
  \def\examplename{Príklad}
  \def\exercisename{Cvičenie}
  \def\lemmaname{Lema}
  \def\notename{Poznámka}
  \def\problemname{Problém}
  \def\propertyname{Vlastnosť}
  \def\questionname{Otázka}
  \def\solutionname{Riešenie}
  \def\lastandname{ a}
\fi

\if@czech
  \def\supervisorname{Školitel}
  \def\keywordsname{Klíčová slova}
  \def\abstractname{Abstrakt}
  \def\refname{Literatura}

  \def\theoremname{Věta}
  \def\casename{Případ}
  \def\conjecturename{Hypotéza}
  \def\corollaryname{Důsledek}
  \def\definitionname{Definice}
  \def\examplename{Příklad}
  \def\exercisename{Cvičení}
  \def\lemmaname{Lema}
  \def\notename{Poznámka}
  \def\problemname{Problém}
  \def\propertyname{Vlastnost}
  \def\questionname{Otázka}
  \def\solutionname{Řešení}
  \def\lastandname{ a}
\fi


% Theorems etc.
\newtheorem{theorem}{\theoremname}{\itshape}{\rmfamily}
\newtheorem{case}{\casename}{\itshape}{\rmfamily}
\newtheorem{conjecture}{\conjecturename}{\itshape}{\rmfamily}
\newtheorem{corollary}{\corollaryname}{\bfseries}{\itshape}
\newtheorem{definition}{\definitionname}{\bfseries}{\itshape}
\newtheorem{example}{\examplename}{\itshape}{\rmfamily}
\newtheorem{exercise}{\exercisename}{\itshape}{\rmfamily}
\newtheorem{lemma}{\lemmaname}{\bfseries}{\itshape}
\newtheorem{note}{\notename}{\itshape}{\rmfamily}
\newtheorem{problem}{\problemname}{\itshape}{\rmfamily}
\newtheorem{property}{\propertyname}{\itshape}{\rmfamily}
\newtheorem{question}{\questionname}{\itshape}{\rmfamily}
\newtheorem{solution}{\solutionname}{\itshape}{\rmfamily}

\def\email#1{{\tt#1}}
\def\homedir{\~{ }}

\def\keywords#1{\unskip\par\smallskip\noindent{\emph{\keywordsname:} #1}}

\renewenvironment{abstract}%
{\thispagestyle{empty}%
\paragraph{\abstractname:}}%
{}

\def\bbbr{{\rm I\!R}} %reelle Zahlen
\def\bbbm{{\rm I\!M}}
\def\bbbn{{\rm I\!N}} %natuerliche Zahlen
\def\bbbf{{\rm I\!F}}
\def\bbbh{{\rm I\!H}}
\def\bbbk{{\rm I\!K}}
\def\bbbp{{\rm I\!P}}
\def\bbbone{{\mathchoice {\rm 1\mskip-4mu l} {\rm 1\mskip-4mu l}
{\rm 1\mskip-4.5mu l} {\rm 1\mskip-5mu l}}}
\def\bbbc{{\mathchoice {\setbox0=\hbox{$\displaystyle\rm C$}\hbox{\hbox
to0pt{\kern0.4\wd0\vrule height0.9\ht0\hss}\box0}}
{\setbox0=\hbox{$\textstyle\rm C$}\hbox{\hbox
to0pt{\kern0.4\wd0\vrule height0.9\ht0\hss}\box0}}
{\setbox0=\hbox{$\scriptstyle\rm C$}\hbox{\hbox
to0pt{\kern0.4\wd0\vrule height0.9\ht0\hss}\box0}}
{\setbox0=\hbox{$\scriptscriptstyle\rm C$}\hbox{\hbox
to0pt{\kern0.4\wd0\vrule height0.9\ht0\hss}\box0}}}}
\def\bbbq{{\mathchoice {\setbox0=\hbox{$\displaystyle\rm
Q$}\hbox{\raise
0.15\ht0\hbox to0pt{\kern0.4\wd0\vrule height0.8\ht0\hss}\box0}}
{\setbox0=\hbox{$\textstyle\rm Q$}\hbox{\raise
0.15\ht0\hbox to0pt{\kern0.4\wd0\vrule height0.8\ht0\hss}\box0}}
{\setbox0=\hbox{$\scriptstyle\rm Q$}\hbox{\raise
0.15\ht0\hbox to0pt{\kern0.4\wd0\vrule height0.7\ht0\hss}\box0}}
{\setbox0=\hbox{$\scriptscriptstyle\rm Q$}\hbox{\raise
0.15\ht0\hbox to0pt{\kern0.4\wd0\vrule height0.7\ht0\hss}\box0}}}}
\def\bbbt{{\mathchoice {\setbox0=\hbox{$\displaystyle\rm
T$}\hbox{\hbox to0pt{\kern0.3\wd0\vrule height0.9\ht0\hss}\box0}}
{\setbox0=\hbox{$\textstyle\rm T$}\hbox{\hbox
to0pt{\kern0.3\wd0\vrule height0.9\ht0\hss}\box0}}
{\setbox0=\hbox{$\scriptstyle\rm T$}\hbox{\hbox
to0pt{\kern0.3\wd0\vrule height0.9\ht0\hss}\box0}}
{\setbox0=\hbox{$\scriptscriptstyle\rm T$}\hbox{\hbox
to0pt{\kern0.3\wd0\vrule height0.9\ht0\hss}\box0}}}}
\def\bbbs{{\mathchoice
{\setbox0=\hbox{$\displaystyle     \rm S$}\hbox{\raise0.5\ht0\hbox
to0pt{\kern0.35\wd0\vrule height0.45\ht0\hss}\hbox
to0pt{\kern0.55\wd0\vrule height0.5\ht0\hss}\box0}}
{\setbox0=\hbox{$\textstyle        \rm S$}\hbox{\raise0.5\ht0\hbox
to0pt{\kern0.35\wd0\vrule height0.45\ht0\hss}\hbox
to0pt{\kern0.55\wd0\vrule height0.5\ht0\hss}\box0}}
{\setbox0=\hbox{$\scriptstyle      \rm S$}\hbox{\raise0.5\ht0\hbox
to0pt{\kern0.35\wd0\vrule height0.45\ht0\hss}\raise0.05\ht0\hbox
to0pt{\kern0.5\wd0\vrule height0.45\ht0\hss}\box0}}
{\setbox0=\hbox{$\scriptscriptstyle\rm S$}\hbox{\raise0.5\ht0\hbox
to0pt{\kern0.4\wd0\vrule height0.45\ht0\hss}\raise0.05\ht0\hbox
to0pt{\kern0.55\wd0\vrule height0.45\ht0\hss}\box0}}}}
\def\bbbz{{\mathchoice {\hbox{$\mathsf\textstyle Z\kern-0.4em Z$}}
{\hbox{$\mathsf\textstyle Z\kern-0.4em Z$}}
{\hbox{$\mathsf\scriptstyle Z\kern-0.3em Z$}}
{\hbox{$\mathsf\scriptscriptstyle Z\kern-0.2em Z$}}}}

%%%%%%%% SECTION HEADINGS LNCS STYLE
\setcounter{secnumdepth}{2}
\renewcommand\section{\@startsection{section}{1}{\z@}%
                       {-18\p@ \@plus -4\p@ \@minus -4\p@}%
                       {12\p@ \@plus 4\p@ \@minus 4\p@}%
                       {\normalfont\large\bfseries\boldmath
                        \rightskip=\z@ \@plus 8em\pretolerance=10000 }}
\renewcommand\subsection{\@startsection{subsection}{2}{\z@}%
                       {-18\p@ \@plus -4\p@ \@minus -4\p@}%
                       {8\p@ \@plus 4\p@ \@minus 4\p@}%
                       {\normalfont\normalsize\bfseries\boldmath
                        \rightskip=\z@ \@plus 8em\pretolerance=10000 }}
\renewcommand\subsubsection{\@startsection{subsubsection}{3}{\z@}%
                       {-18\p@ \@plus -4\p@ \@minus -4\p@}%
                       {-0.5em \@plus -0.22em \@minus -0.1em}%
                       {\normalfont\normalsize\bfseries\boldmath}}
\renewcommand\paragraph{\@startsection{paragraph}{4}{\z@}%
                       {-12\p@ \@plus -4\p@ \@minus -4\p@}%
                       {-0.5em \@plus -0.22em \@minus -0.1em}%
                       {\normalfont\normalsize\itshape}}
\renewcommand\subparagraph[1]{\typeout{LLNCS warning: You should not use
                  \string\subparagraph\space with this class}\vskip0.5cm
You should not use \verb|\subparagraph| with this class.\vskip0.5cm}


\newcounter{@auth}
\newcounter{auco}

\def\@maketitle{\newpage
 \markboth{}{}%
 \def\lastand{\ifnum\value{@inst}=2\relax
                 \unskip{} \andname\
              \else
                 \unskip \lastandname\
              \fi}%
 \def\and{\stepcounter{@auth}\relax
          \ifnum\value{@auth}=\value{@inst}%
             \lastand
          \else
             \unskip,
          \fi}%
 \begin{center}%
 \let\newline\\
 {\Large \bfseries\boldmath
  \pretolerance=10000
  \@title \par}\vskip .8cm
 \setbox0=\vbox{\setcounter{@auth}{1}\def\and{\stepcounter{@auth}}%
 \def\thanks##1{}\@author}%
 \global\value{@inst}=\value{@auth}%
 \global\value{auco}=\value{@auth}%
 \setcounter{@auth}{1}%
{\lineskip .5em
\noindent\ignorespaces
\@author\vskip.35cm}
 {\small\institutename}
 \end{center}%
 }



\pagenumbering{gobble}




% EOF
\endinput
