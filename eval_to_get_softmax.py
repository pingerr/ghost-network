from config import config as FLAGS
from networks import network
from utils import *


def eval_once(result_dir=FLAGS.result_dir):
    accs = []
    sess = tf.Session()
    for network_name in FLAGS.test_network:
        save_name = network_name
        if FLAGS.random_range > 0:
            save_name += "_{:.3f}".format(FLAGS.random_range)

        if FLAGS.keep_prob < 1:
            save_name += "_keep{:.3f}".format(FLAGS.keep_prob)
        save_path = os.path.join("softmax_result", save_name)

        print("evaluating {:s}..., will save at {:s}".format(network_name, save_path))

        # building graph
        x_input = tf.placeholder(tf.float32, (None, 299, 299, 3))
        logit, preds = network.model(sess, x_input, network_name)
        softmax_tensor =tf.nn.softmax(logit)

        # loading and saving related
        correct_num = 0.
        xs = load_data(FLAGS.test_list_filename)
        ys = get_label(xs, FLAGS.ground_truth_file)
        x_batches = split_to_batches(xs, FLAGS.batch_size)
        y_batches = split_to_batches(ys, FLAGS.batch_size)
        softmaxs = []

        for batch_index, (x_batch, y_batch) in enumerate(zip(x_batches, y_batches)):
            images = load_images(x_batch, result_dir)
            gt_labels = y_batch
            labels, softmax = sess.run([preds, softmax_tensor], {x_input: images})
            correct_num += np.sum(labels == gt_labels)
            assert np.abs(np.sum(softmax[0,:]) - 1) < 1e-5, "{:.6f}".format(np.sum(softmax[0,:]))
            softmaxs.append(softmax)

        softmaxs = np.concatenate(softmaxs)
        acc = correct_num / len(xs)
        print("{:s}: {:.2f}%".format(network_name, 100 - acc * 100))
        accs.append(1 - acc)

        np.save(save_path, softmaxs)

        # tf.reset_default_graph()
        # network._network_initialized[network_name] = False
    sess.close()

    ndprint(FLAGS.test_network, "{:s}, ")
    ndprint(np.array(accs) * 100)

    import datetime

    now = datetime.datetime.now()
    with open("eval_results.txt", "a+") as f:
        if FLAGS.eval_clean:
            f.writelines("{:s}, eval_clean {:.3f},".format(str(now), FLAGS.random_range))
        else:
            f.writelines("{:s}, {:s},".format(str(now), result_dir))
        f.writelines(" {:s}\n".format(ndstr(np.array(accs) * 100)))


if __name__ == '__main__':
    assert FLAGS.eval_clean
    eval_once()
