\NeedsTeXFormat{LaTeX2e}[2011/06/27]
\ProvidesClass{stellingen}[2012/10/16 v0 Stellingen behorende bij proefschrift]

% Magic default values
\newcommand\@ptsize{}

% Standard options
\DeclareOption{10pt}{\renewcommand\@ptsize{0}}
\DeclareOption{11pt}{\renewcommand\@ptsize{1}}
\DeclareOption{12pt}{\renewcommand\@ptsize{2}}
\DeclareOption{draft}{\setlength\overfullrule{5pt}}
\DeclareOption{final}{\setlength\overfullrule{0pt}}

\ExecuteOptions{10pt,final}
\ProcessOptions

% Force 'twoside' and 'onecolumn'
\@twosidefalse
\@mparswitchtrue
\@twocolumnfalse

% Input the type size
\input{size1\@ptsize.clo}
\setlength\lineskip{1\p@}
\setlength\normallineskip{1\p@}
\renewcommand\baselinestretch{}
\setlength\parskip{0\p@ \@plus \p@}

% Set spacing
\setlength\parindent{0\p@}
\setlength\smallskipamount{3\p@ \@plus 1\p@ \@minus 1\p@}
\setlength\medskipamount{6\p@ \@plus 2\p@ \@minus 2\p@}
\setlength\bigskipamount{12\p@ \@plus 4\p@ \@minus 4\p@}
\setlength\headheight{12\p@}
\setlength\headsep{25\p@}
\setlength\topskip{10\p@}
\setlength\footskip{30\p@}
\setlength\maxdepth{.5\topskip}

% Spacing penalties
\@lowpenalty 51
\@medpenalty 151
\@highpenalty 301
\setcounter{topnumber}{2}
\renewcommand\topfraction{.7}
\setcounter{bottomnumber}{1}
\renewcommand\bottomfraction{.3}
\setcounter{totalnumber}{3}
\renewcommand\textfraction{.2}
\renewcommand\floatpagefraction{.5}
\setcounter{dbltopnumber}{2}
\renewcommand\dbltopfraction{.7}
\renewcommand\dblfloatpagefraction{.5}

% Other packages
\RequirePackage[a5paper,margin=2cm,nohead,nofoot]{geometry}
\RequirePackage{fancyhdr}
\RequirePackage{xparse}  % for \NewDocumentEnvironment
\RequirePackage{textcase}  % for \MakeTextUppercase

% Running heads
\pagestyle{empty}
\pagenumbering{arabic}

% Odds'n'ends
\def\today{\ifcase\month\or
	January\or February\or March\or April\or May\or June\or
	July\or August\or September\or October\or
	November \or December\fi \space\number\day, \number\year}
\raggedbottom
\onecolumn

% Customization hooks
\newcommand\stellingenstyle[1]{\Large #1}
\newcommand\behorendestyle[1]{#1}
\newcommand\titlestyle[1]{\LARGE\bfseries\MakeTextUppercase{#1}}
\newcommand\numberingstyle[1]{\bfseries #1}
\newcommand\codastyle[1]{\itshape #1}
\newcommand\sourcestyle[1]{\emph{#1}}
\newcommand\stellingenstring{Stellingen}
\newcommand\behorendestring{behorende bij het proefschrift}
% Secret customization hook
\newcommand\stelling@printnumbering{\centering\numberingstyle{\Roman{destelling}}}

% Title
\newcommand\maketitle{\par
	\begingroup
		\newpage
		\global\@topnum\z@  % Prevents figures from going at top of page
		\@maketitle
		\@thanks
	\endgroup
	\global\let\maketitle\relax
	\global\let\@maketitle\relax
	\global\let\@title\@empty
	\global\let\title\relax

}
\def\@maketitle{%
	\begin{center}
		{\stellingenstyle{\stellingenstring} \par}%
		{\behorendestyle{\behorendestring} \par}%
		{\titlestyle{\@title} \par}%
	\end{center}%
	\par
	\vskip 1.5em}

% 'stelling' environment
\newcounter{destelling}
\setcounter{destelling}{1}
\NewDocumentEnvironment{stelling}{+o}{%
	\begin{minipage}{\textwidth}%
		{\stelling@printnumbering\par}%
		\stepcounter{destelling}%
}{%
		\IfNoValueTF{#1}{}{%
			\begin{flushright}%
				\sourcestyle{#1}%
			\end{flushright}%
		}%
	\end{minipage}%
	\vskip 1.5em
}

% Coda
\AtEndDocument{%
	\begin{center}
		\codastyle{\@author} \par
		\codastyle{\@date}
	\end{center}
	\global\let\@author\@empty
	\global\let\@date\@empty
	\global\let\author\relax
	\global\let\date\relax
	\global\let\and\relax
}
