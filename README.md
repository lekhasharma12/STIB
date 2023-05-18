# Spill the Implicit Beans : Interpreting figurative texts using prompting

"Spill the implicit beans" or STIB is project to leverage different prompting strategies to get better literal translations for figurative language types, specifically Metaphor, Idiom, Simile and Sarcasm.

We use zero-shot prompting as our baseline and then test few-shot prompting, intruction promting and chain of thought prompting to compare performances across these strategies. We also classify these fiurative sentences and add the type in these prompts to check if knowing the type of figuartive sentence helps to generate better literal translations.

Our Dataset folder consists of train and test data for both Classification and Prompting.

Our Code folder is also divided into Classifiaction and Prompting folders and each of them consists of separate code files for each strategy of classification and prompting clearly specified by the file name.
